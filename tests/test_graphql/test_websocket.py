
def test_websocket_connection_bare(authorized_client):
    client =authorized_client
    with client.websocket_connect('/graphql', subprotocols=[ "graphql-transport-ws","graphql-ws"] ) as websocket:
        assert websocket is not None
        assert websocket.scope is not None
