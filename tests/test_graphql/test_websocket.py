from tests.common import generate_jobs_subscription

# from selfprivacy_api.graphql.subscriptions.jobs import JobSubscriptions
import pytest
import asyncio

from selfprivacy_api.jobs import Jobs
from time import sleep

from tests.test_redis import empty_redis

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


def init_graphql(websocket):
    websocket.send_json({"type": "connection_init", "payload": {}})
    ack = websocket.receive_json()
    assert ack == {"type": "connection_ack"}


def test_websocket_subscription_minimal(authorized_client):
    client = authorized_client
    with client.websocket_connect(
        "/graphql", subprotocols=["graphql-transport-ws"]
    ) as websocket:
        init_graphql(websocket)
        websocket.send_json(
            {
                "id": "3aaa2445",
                "type": "subscribe",
                "payload": {
                    "query": "subscription TestSubscription {count}",
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "id": "3aaa2445",
            "payload": {"data": {"count": 0}},
            "type": "next",
        }
        response = websocket.receive_json()
        assert response == {
            "id": "3aaa2445",
            "payload": {"data": {"count": 1}},
            "type": "next",
        }
        response = websocket.receive_json()
        assert response == {
            "id": "3aaa2445",
            "payload": {"data": {"count": 2}},
            "type": "next",
        }


async def read_one_job(websocket):
    # bug? We only get them starting from the second job update
    # that's why we receive two jobs in the list them
    # the first update gets lost somewhere
    response = websocket.receive_json()
    return response


@pytest.mark.asyncio
async def test_websocket_subscription(authorized_client, empty_redis, event_loop):
    client = authorized_client
    with client.websocket_connect(
        "/graphql", subprotocols=["graphql-transport-ws"]
    ) as websocket:
        init_graphql(websocket)
        websocket.send_json(
            {
                "id": "3aaa2445",
                "type": "subscribe",
                "payload": {
                    "query": "subscription TestSubscription {"
                    + JOBS_SUBSCRIPTION
                    + "}",
                },
            }
        )
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
