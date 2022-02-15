from pytest_mock import MockFixture

from opta.utils.markdown import Code, Markdown, Text, Title1, Title2


class TestMarkdown:
    def test_header(self, mocker: MockFixture) -> None:
        readme = Markdown()
        readme >> Title1("header 1")
        assert (
            f"{readme}"
            == """# header 1

"""
        )
        readme = Markdown()
        readme >> Title2("header 1.1")
        assert (
            f"{readme}"
            == """## header 1.1

"""
        )

    def test_code(self, mocker: MockFixture) -> None:
        readme = Markdown()
        readme >> Code("bla")
        assert (
            f"{readme}"
            == """```
bla
```

"""
        )

        readme = Markdown()
        readme >> Code('{"Hello":"World"}', "json")
        assert (
            f"{readme}"
            == """```json
{"Hello":"World"}
```

"""
        )

    def test_text(self, mocker: MockFixture) -> None:
        readme = Markdown()
        readme >> Text("some text")
        assert f"{readme}" == "some text  \n\n"
        readme = Markdown()
        readme >> Text(
            """line 1
        line2"""
        )
        assert f"{readme}" == "line 1\nline2  \n\n"

    def test_all_together(self, mocker: MockFixture) -> None:
        readme = Markdown()
        readme >> Title1("first header")
        readme >> Text(
            "This step will execute terraform for the modules `base`, `k8scluster`."
        )
        readme >> Code(
            """echo a
        a""",
            "shell",
        )

        assert (
            f"{readme}"
            == """# first header
"""
            "\nThis step will execute terraform for the modules `base`, `k8scluster`.  "  # noqa: W291
            """\n
```shell
echo a
a
```

"""
        )
