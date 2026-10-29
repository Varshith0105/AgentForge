import pytest


def test_websocket_connection_refused_without_token(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/main"):
            pass
