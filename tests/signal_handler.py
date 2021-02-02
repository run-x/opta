# type: ignore
import os
import signal
import sys
import time


def signal_handler(sig, frame):
    print("You pressed Ctrl+C!")
    time.sleep(1)
    with open(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "tests",
            "signal_gracefully_terminated",
        ),
        "w",
    ) as f:
        f.write("blah")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
print("Press Ctrl+C")
signal.pause()
