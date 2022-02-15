import time
from os import environ

from websocket import WebSocket

ws = WebSocket()
HOST: str = environ.get("HOST", "")
retry_count = 0
while True:
    try:
        ws.connect(f"ws://{HOST}/websocket")
        test_message = "Test WebSocket"
        ws.send(test_message)
        actual_result = ws.recv()
        expected_result = f"Server received from client: {test_message}"
        assert expected_result == actual_result
        exit(0)
    except Exception as e:
        if retry_count < 15:
            print(f"Got exception {e}. Retrying in a bit")
            time.sleep(retry_count)
            retry_count += 1
        else:
            print(e)
            exit(1)
