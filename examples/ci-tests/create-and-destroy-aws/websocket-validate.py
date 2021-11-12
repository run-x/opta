from os import environ

from websocket import WebSocket

ws = WebSocket()
HOST: str = environ.get("HOST", "")
try:
    ws.connect(f"ws://{HOST}/websocket")
    test_message = "Test WebSocket"
    ws.send(test_message)
    actual_result = ws.recv()
    expected_result = f"Server received from client: {test_message}"
    assert expected_result == actual_result
    exit(0)
except Exception:
    exit(1)
