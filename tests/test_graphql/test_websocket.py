from tests.common import generate_jobs_subscription
from selfprivacy_api.graphql.queries.jobs import Job as _Job
from selfprivacy_api.jobs import Jobs

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


# def test_websocket_subscription(authorized_client):
#     client = authorized_client
#     with client.websocket_connect(
#         "/graphql", subprotocols=["graphql-transport-ws"]
#     ) as websocket:
#         init_graphql(websocket)
#         websocket.send_json(
#             {
#                 "id": "3aaa2445",
#                 "type": "subscribe",
#                 "payload": {
#                     "query": generate_jobs_subscription([JOBS_SUBSCRIPTION]),
#                 },
#             }
#         )
#         Jobs.add("bogus", "bogus.bogus", "yyyaaaaayy")
#         response = websocket.receive_json()
#         raise NotImplementedError(response)
