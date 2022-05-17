"""
This module can generate some markdown (.md) output
"""


from typing import List, Optional

import markdown as markdown_lib


class Text:

    # note: the 2 extra spaces means a line break
    def __init__(self, text: str, prefix: str = "", suffix: str = "  \n") -> None:
        self.text = text
        self.prefix = prefix
        self.suffix = suffix

    def format(self) -> str:
        #  by default strip line to ignore identation, makes it easier to instantiate
        content = "\n".join([s.strip() for s in self.text.splitlines()])
        return f"{self.prefix}{content}{self.suffix}"

    def __str__(self) -> str:
        return self.format()


class Markdown:
    def __init__(self) -> None:
        self.texts: List[Text] = []

    def __rshift__(self, text: Text) -> None:
        self.texts.append(text)

    def __str__(self) -> str:
        strings = [str(elmt) for elmt in self.texts]
        return "\n".join(strings) + "\n"

    def write(self, path: str) -> None:
        """write to file"""
        Markdown._write(path, str(self))

    def writeHTML(self, path: str) -> None:
        """write to html file"""
        html = markdown_lib.markdown(str(self))
        Markdown._write(path, html)

    @staticmethod
    def _write(path: str, content: str) -> None:
        """write to file"""
        with open(path, "w") as f:
            f.write(content)


class Title1(Text):
    def __init__(self, text: str) -> None:
        super().__init__(text, "# ", "\n")


class Title2(Text):
    def __init__(self, text: str) -> None:
        super().__init__(text, "## ", "\n")


class Code(Text):
    def __init__(self, text: str, lang: Optional[str] = None) -> None:
        lang = "" if lang is None else lang
        super().__init__(text, f"```{lang}\n", "\n```\n")
