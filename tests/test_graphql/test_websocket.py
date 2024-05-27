# from selfprivacy_api.graphql.subscriptions.jobs import JobSubscriptions
import pytest
import asyncio
from typing import Generator
from time import sleep

from starlette.testclient import WebSocketTestSession

from selfprivacy_api.jobs import Jobs
from selfprivacy_api.actions.api_tokens import TOKEN_REPO
from selfprivacy_api.graphql import IsAuthenticated

from tests.conftest import DEVICE_WE_AUTH_TESTS_WITH
from tests.test_jobs import jobs as empty_jobs

# We do not iterate through them yet
TESTED_SUBPROTOCOLS = ["graphql-transport-ws"]

JOBS_SUBSCRIPTION = """
jobUpdates {
    uid
    typeId
    name
    description
    status
    statusText
    progress
    createdAt
    updatedAt
    finishedAt
    error
    result
}
"""


def connect_ws_authenticated(authorized_client) -> WebSocketTestSession:
    token = "Bearer " + str(DEVICE_WE_AUTH_TESTS_WITH["token"])
    return authorized_client.websocket_connect(
        "/graphql",
        subprotocols=TESTED_SUBPROTOCOLS,
        params={"token": token},
    )


def connect_ws_not_authenticated(client) -> WebSocketTestSession:
    return client.websocket_connect(
        "/graphql",
        subprotocols=TESTED_SUBPROTOCOLS,
        params={"token": "I like vegan icecream but it is not a valid token"},
    )


def init_graphql(websocket):
    websocket.send_json({"type": "connection_init", "payload": {}})
    ack = websocket.receive_json()
    assert ack == {"type": "connection_ack"}


@pytest.fixture
def authenticated_websocket(
    authorized_client,
) -> Generator[WebSocketTestSession, None, None]:
    # We use authorized_client only tohave token in the repo, this client by itself is not enough to authorize websocket

    ValueError(TOKEN_REPO.get_tokens())
    with connect_ws_authenticated(authorized_client) as websocket:
        yield websocket
        sleep(1)


@pytest.fixture
def unauthenticated_websocket(client) -> Generator[WebSocketTestSession, None, None]:
    with connect_ws_not_authenticated(client) as websocket:
        yield websocket
        sleep(1)


def test_websocket_connection_bare(authorized_client):
    client = authorized_client
    with client.websocket_connect(
        "/graphql", subprotocols=["graphql-transport-ws", "graphql-ws"]
    ) as websocket:
        assert websocket is not None
        assert websocket.scope is not None


def test_websocket_graphql_init(authorized_client):
    client = authorized_client
    with client.websocket_connect(
        "/graphql", subprotocols=["graphql-transport-ws"]
    ) as websocket:
        websocket.send_json({"type": "connection_init", "payload": {}})
        ack = websocket.receive_json()
        assert ack == {"type": "connection_ack"}


def test_websocket_graphql_ping(authorized_client):
    client = authorized_client
    with client.websocket_connect(
        "/graphql", subprotocols=["graphql-transport-ws"]
    ) as websocket:
        # https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md#ping
        websocket.send_json({"type": "ping", "payload": {}})
        pong = websocket.receive_json()
        assert pong == {"type": "pong"}


def api_subscribe(websocket, id, subscription):
    websocket.send_json(
        {
            "id": id,
            "type": "subscribe",
            "payload": {
                "query": "subscription TestSubscription {" + subscription + "}",
            },
        }
    )


def test_websocket_subscription_minimal(authorized_client):
    # Test a small endpoint that exists specifically for tests
    client = authorized_client
    with client.websocket_connect(
        "/graphql", subprotocols=["graphql-transport-ws"]
    ) as websocket:
        init_graphql(websocket)
        arbitrary_id = "3aaa2445"
        api_subscribe(websocket, arbitrary_id, "count")
        response = websocket.receive_json()
        assert response == {
            "id": arbitrary_id,
            "payload": {"data": {"count": 0}},
            "type": "next",
        }
        response = websocket.receive_json()
        assert response == {
            "id": arbitrary_id,
            "payload": {"data": {"count": 1}},
            "type": "next",
        }
        response = websocket.receive_json()
        assert response == {
            "id": arbitrary_id,
            "payload": {"data": {"count": 2}},
            "type": "next",
        }


def test_websocket_subscription_minimal_unauthorized(unauthenticated_websocket):
    websocket = unauthenticated_websocket
    init_graphql(websocket)
    arbitrary_id = "3aaa2445"
    api_subscribe(websocket, arbitrary_id, "count")

    response = websocket.receive_json()
    assert response == {
        "id": arbitrary_id,
        "payload": [{"message": IsAuthenticated.message}],
        "type": "error",
    }


async def read_one_job(websocket):
    # bug? We only get them starting from the second job update
    # that's why we receive two jobs in the list them
    # the first update gets lost somewhere
    response = websocket.receive_json()
    return response


@pytest.mark.asyncio
async def test_websocket_subscription(authenticated_websocket, event_loop, empty_jobs):
    websocket = authenticated_websocket
    init_graphql(websocket)
    arbitrary_id = "3aaa2445"
    api_subscribe(websocket, arbitrary_id, JOBS_SUBSCRIPTION)

    future = asyncio.create_task(read_one_job(websocket))
    jobs = []
    jobs.append(Jobs.add("bogus", "bogus.bogus", "yyyaaaaayy it works"))
    sleep(0.5)
    jobs.append(Jobs.add("bogus2", "bogus.bogus", "yyyaaaaayy it works"))

    response = await future
    data = response["payload"]["data"]
    jobs_received = data["jobUpdates"]
    received_names = [job["name"] for job in jobs_received]
    for job in jobs:
        assert job.name in received_names

    assert len(jobs_received) == 2

    for job in jobs:
        for api_job in jobs_received:
            if (job.name) == api_job["name"]:
                assert api_job["uid"] == str(job.uid)
                assert api_job["typeId"] == job.type_id
                assert api_job["name"] == job.name
                assert api_job["description"] == job.description
                assert api_job["status"] == job.status
                assert api_job["statusText"] == job.status_text
                assert api_job["progress"] == job.progress
                assert api_job["createdAt"] == job.created_at.isoformat()
                assert api_job["updatedAt"] == job.updated_at.isoformat()
                assert api_job["finishedAt"] == None
                assert api_job["error"] == None
                assert api_job["result"] == None


def test_websocket_subscription_unauthorized(unauthenticated_websocket):
    websocket = unauthenticated_websocket
    init_graphql(websocket)
    id = "3aaa2445"
    api_subscribe(websocket, id, JOBS_SUBSCRIPTION)

    response = websocket.receive_json()
    assert response == {
        "id": id,
        "payload": [{"message": IsAuthenticated.message}],
        "type": "error",
    }
