import atexit
import inspect
import os
import sys
import textwrap
from asyncio import Lock, iscoroutinefunction
from functools import wraps
from math import ceil, floor, log10
from time import time as unix_time
from typing import Any, Callable, Dict, Final, List, Tuple, TypedDict
from uuid import UUID, uuid4

from colored import attr, fg


def round_sig(x: float, sig: int = 3) -> float:
    return round(x, sig - int(floor(log10(abs(x)))) - 1)


class TimedCall(TypedDict):
    id: UUID
    function_name: str
    positional_args: Tuple[Any, ...]
    keyword_args: Dict[str, Any]
    start_time: float
    end_time: float
    caller_file: str
    caller_line: int


_records: List[TimedCall] = []
ASYNC_LOCK: Final = Lock()
REPORT_SIZE: Final = 20
TIME_THRESHOLD: Final = 0.1
REPORT_ENABLED: bool = True
BLOCK_SYMBOL: Final = "\u2588"
START_TIME: Final = unix_time()


def time(func: Callable) -> Callable:
    if iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args: Any, **kwds: Any) -> Any:
            if not REPORT_ENABLED:
                return await func(*args, **kwds)
            frame_info = inspect.stack()[1]
            start_time = unix_time()
            output = await func(*args, **kwds)
            end_time = unix_time()
            if end_time - start_time <= TIME_THRESHOLD:
                return output
            _records.append(
                {
                    "function_name": func.__name__,
                    "positional_args": args,
                    "keyword_args": kwds,
                    "start_time": start_time,
                    "end_time": end_time,
                    "id": uuid4(),
                    "caller_file": "/".join(frame_info.filename.split("/")[-2:]),
                    "caller_line": frame_info.lineno,
                }
            )
            print(
                f"{fg('green')}Meister{attr(0)}: Function {func.__name__} took {end_time - start_time} seconds"
            )
            return output

    else:

        @wraps(func)
        def wrapper(*args: Any, **kwds: Any) -> Any:
            if not REPORT_ENABLED:
                return func(*args, **kwds)
            frame_info = inspect.stack()[1]
            start_time = unix_time()
            output = func(*args, **kwds)
            end_time = unix_time()
            if end_time - start_time <= TIME_THRESHOLD:
                return output
            _records.append(
                {
                    "id": uuid4(),
                    "function_name": func.__name__,
                    "positional_args": args,
                    "keyword_args": kwds,
                    "start_time": start_time,
                    "end_time": end_time,
                    "caller_file": "/".join(frame_info.filename.split("/")[-2:]),
                    "caller_line": frame_info.lineno,
                }
            )
            print(
                f"{fg('green')}Meister{attr(0)}: Function {func.__name__} took {round_sig(end_time - start_time)} seconds"
            )
            return output

    return wrapper


def make_report() -> None:
    if not REPORT_ENABLED or hasattr(sys, "_called_from_test"):
        return
    end_time = unix_time()
    total_time = end_time - START_TIME
    sorted_records = sorted(
        _records, key=lambda x: x["end_time"] - x["start_time"], reverse=True
    )
    sorted_records = sorted_records[:REPORT_SIZE]
    print(
        f"{fg('green')}Meister Report{attr(0)}: Total time: {round_sig(total_time)} seconds. Here are the top "
        f"{min(REPORT_SIZE, len(sorted_records))} longest function calls"
    )
    color_map: Dict[UUID, int] = {}
    for idx, record in enumerate(sorted_records):
        color_idx = 2 + (idx % 254)
        positional_args_str = str(record["positional_args"])
        positional_args_str = textwrap.shorten(
            positional_args_str, width=40, placeholder="..."
        )
        keyword_args_str = str(record["keyword_args"])
        keyword_args_str = textwrap.shorten(keyword_args_str, width=40, placeholder="...")
        print(
            f"{fg(color_idx)}{record['function_name']}{attr(0)} called in file {record['caller_file']}, line {record['caller_line']} with args {positional_args_str}, "
            f"kwargs {keyword_args_str}: {round_sig(record['end_time'] - record['start_time'])} seconds"
        )
        color_map[record["id"]] = color_idx
    try:
        max_column = os.get_terminal_size()[0]
    except OSError:
        max_column = 80  # Assume 80 columns if we aren't in a terminal
    sorted_records = sorted(sorted_records, key=lambda x: x["start_time"])
    lane_printer = GreedyLanePrinter()
    for record in sorted_records:
        lane_object: LaneObject = {
            "start": floor((record["start_time"] - START_TIME) / total_time * max_column),
            "end": ceil((record["end_time"] - START_TIME) / total_time * max_column),
            "color_idx": color_map[record["id"]],
        }
        lane_printer.add_entry(lane_object)
    lane_printer.render()


class LaneObject(TypedDict):
    start: int
    end: int
    color_idx: int


class GreedyLanePrinter:
    """Only works nicely if you add from smallest number to largest"""

    def __init__(self) -> None:
        self.lanes: List[List[LaneObject]] = []

    def add_entry(self, lane_object: LaneObject) -> None:
        for lane in self.lanes:
            last_object = lane[-1]
            if last_object["end"] <= lane_object["start"]:
                lane.append(lane_object)
                return
        self.lanes.append([lane_object])

    def render(self) -> None:
        for lane in self.lanes:
            lane_string = f"{fg(0)}{BLOCK_SYMBOL * lane[0]['start']}{attr(0)}"
            for lane_object in lane:
                blocks = BLOCK_SYMBOL * (lane_object["end"] - lane_object["start"])
                lane_string += f"{fg(lane_object['color_idx'])}{blocks}{attr(0)}"
            print(lane_string)


atexit.register(make_report)
