import os
from typing import Dict, List

from pick import Picker
from rich.console import Console
from rich.markdown import Markdown

from opta.constants import DEBUG_TREE


class Debugger:
    def __init__(self) -> None:
        self.path: List[int] = []
        self.console: Console = Console()

    def run(self) -> None:
        while True:
            cur_context = self.current_context()
            with open(
                f"{os.path.dirname(__file__)}/../{cur_context['textfile']}"
            ) as text:
                markdown = Markdown(text.read())
            with self.console.capture() as capture:
                self.console.print(markdown)
            helper_text = capture.get()
            children_paths: List = cur_context.get("children", [])

            options = [child["name"] for child in children_paths]
            if not self.path:
                options.append("I'm gonna go now")
            else:
                options.append("Take me back to the last screen")
            picker = Picker(options, helper_text + "\nWhat's on your mind?")
            _, index = picker.start()
            if index == len(children_paths):
                if self.path:
                    self.path.pop()
                else:
                    self.console.print("Stay awesome, buddy.")
                    exit(0)
            else:
                self.path.append(index)

    def current_context(self) -> Dict:
        cur_context = DEBUG_TREE.copy()
        for idx in self.path:
            cur_context = cur_context["children"][idx]
        return cur_context
