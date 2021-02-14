import logging
import sys
from shutil import which
from textwrap import dedent
from typing import Any, Dict, List

from opta.special_formatter import PartialFormatter

logger = logging.getLogger("opta")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(levelname)s: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


fmt = PartialFormatter("")


def deep_merge(a: Dict[Any, Any], b: Dict[Any, Any]) -> Dict[Any, Any]:
    b = b.copy()
    for key, value in a.items():
        if key in b:
            if isinstance(value, dict) and isinstance(b[key], dict):
                b[key] = deep_merge(value, b[key])
            elif value != b[key]:
                raise Exception(f"Cant merge conflicting non-dict values (key: {key})")
        else:
            b[key] = value

    return b


def hydrate(target: Any, hydration: Dict[Any, Any]) -> Dict[Any, Any]:
    if isinstance(target, dict):
        target = target.copy()
        for k, v in target.items():
            target[k] = hydrate(v, hydration)
    elif isinstance(target, list):
        target = [hydrate(x, hydration) for x in target]
    elif isinstance(target, str):
        target = fmt.format(target, **hydration)

    return target


def is_tool(name: str) -> bool:
    """Check whether `name` is on PATH and marked as executable."""
    return which(name) is not None


def safe_run(func):  # type: ignore
    def func_wrapper(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if hasattr(sys, "_called_from_test"):
                raise e
            else:
                print(e)
                return None

    return func_wrapper


def fmt_msg(message: str) -> str:
    """Format triple quote python strings"""
    # TODO: Replace with better message formatting
    message = dedent(message)
    message = message.replace("\n", " ")
    message = message.replace("~", "\n")
    return message


# TODO: Support max-width.
# The data should be a 2D array of the shape rows x columns.
def column_print(data: List[Any]) -> None:
    # Determine the width of each column (the length of the longest word + 1)
    longest_char_len_by_column = [0] * len(data[0])
    for row in data:
        for column_idx, word in enumerate(row):
            longest_char_len_by_column[column_idx] = max(
                len(word), longest_char_len_by_column[column_idx]
            )

    # Create each line of output one at a time.
    lines = []
    for row in data:
        line = []
        for column_idx, word in enumerate(row):
            line.append(word.ljust(longest_char_len_by_column[column_idx]))
        line_out = " ".join(line)
        lines.append(line_out)

    print("\n".join(lines))


# Get all substrings separated by the delimiter.
# Ex: "foo.bar.baz", delimiter = "."
# -> ['foo', 'foo.bar', 'foo.bar.baz', 'bar.baz', 'bar', 'bar.baz', 'baz']
def all_substrings(string: str, delimiter: str = "") -> List[str]:
    all_substrings = []
    words = string.split(delimiter) if len(delimiter) else list(string)

    def add_words(i: int, j: int) -> None:
        if j > len(words):
            return
        substring = delimiter.join(words[i:j])
        all_substrings.append(substring)
        add_words(i, j + 1)
        add_words(i + 1, j + 1)

    add_words(0, 1)
    return all_substrings
