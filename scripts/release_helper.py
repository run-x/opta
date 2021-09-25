#!/usr/bin/env python
import curses
import os
import re
import tempfile
from curses import window
from subprocess import call
from typing import List, Optional

import click
import semver
from colored import attr, fg
from github import Github, GithubException
from github.Commit import Commit
from github.GitRef import GitRef
from github.GitRelease import GitRelease
from github.PullRequest import PullRequest
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.compat import StringIO

yaml = YAML(typ="safe")
KEYS_ENTER = (curses.KEY_ENTER, ord("\n"), ord("\r"))
KEYS_UP = (curses.KEY_UP, ord("k"))
KEYS_DOWN = (curses.KEY_DOWN, ord("j"))

RELEASE_TEMPLATE = """# Description
{description}

# Commits Present
{commit_list_lines}

# Breaking Changes
{breaking_changes_lines}

# Downtime Changes
{downtime_changes_lines}

# Dataloss Changes
{dataloss_changes_lines}
"""


class ReleaseHelper:
    def __init__(self) -> None:
        github_token = os.getenv("OPTA_GITHUB_TOKEN", None)
        while True:
            if github_token is None or not self.verify_github_token(github_token):
                github_token = click.prompt(
                    "To continue we will need you pass in one of your github api tokens w/ write access to the "
                    "opta repo (you can also set the OPTA_GITHUB_TOKEN env var)",
                    hide_input=True,
                )
            else:
                break
        self.github_client = Github(github_token)
        self.opta_repo = self.github_client.get_repo("run-x/opta")
        self.screen: Optional[window] = None
        self.release_title = "Awesome Title"
        self.release_description = "TBD"
        self.breaking_changes: List[str] = []
        self.downtime_changes: List[str] = []
        self.dataloss_changes: List[str] = []
        self.latest_release = self.opta_repo.get_latest_release()
        self.index = 0

        tag_ref: GitRef = self.opta_repo.get_git_matching_refs(
            "tags/" + self.latest_release.tag_name
        )[0]
        commit_sha = tag_ref.object.sha
        self.last_release_commit = self.opta_repo.get_commit(commit_sha)
        self.commits_since_last_release = [
            x
            for x in self.opta_repo.get_commits(
                since=self.last_release_commit.commit.author.date
            )
        ][:-1]
        for commit in self.commits_since_last_release:
            self.fill_in_commit_defaults(commit)

        self.commit_titles = [
            commit.commit.message.split("\n")[0]
            for commit in self.commits_since_last_release
        ]
        self.options: List[str] = []
        self.release_tag = self.get_default_tag()
        self.refresh_options()

    def refresh_options(self) -> None:
        options: List[str] = []
        options.extend(
            [f'I want to checkout more of commit "{x}"' for x in self.commit_titles]
        )
        options.append(f"I want to change the tag from {self.release_tag}")
        options.append(f"I want to update the release title from {self.release_title}")
        options.append("I want to update the release description")
        options.append("I want to update the breaking changes list")
        options.append("I want to update the downtime changes list")
        options.append("I want to udpate the data loss changes list")
        options.append("I want to finalize the draft")
        options.append("Exit")
        self.options = options

    def get_default_tag(self) -> str:
        try:
            if (
                len(self.downtime_changes + self.breaking_changes + self.dataloss_changes)
                == 0
            ):
                return "v" + str(
                    semver.VersionInfo.parse(
                        self.latest_release.tag_name.strip("v")
                    ).bump_patch()
                )
            else:
                return "v" + str(
                    semver.VersionInfo.parse(
                        self.latest_release.tag_name.strip("v")
                    ).bump_minor()
                )
        except Exception:
            return "WIP"

    def fill_in_commit_defaults(self, commit: Commit) -> None:
        pull_requests: List[PullRequest] = [x for x in commit.get_pulls()]  # type: ignore
        is_breaking = True
        is_downtime = True
        is_dataloss = True
        commit_title = commit.commit.message.split("\n")[0]

        if len(pull_requests) > 0:
            pull_request = pull_requests[0]
            body = pull_request.body
            is_breaking = (
                re.search(
                    ".*\\* \\[( *)[xX]( *)\\] This change is backwards compatible and safe to apply by existing users.*",
                    body,
                )
                is None
            )
            is_dataloss = (
                re.search(
                    ".*\\* \\[( *)[xX]( *)\\] This change will NOT lead to data loss.*",
                    body,
                )
                is None
            )
            is_downtime = (
                re.search(
                    ".*\\* \\[( *)[xX]( *)\\] This change will NOT lead to downtime who already has an env/service setup.*",
                    body,
                )
                is None
            )

        if is_downtime:
            self.downtime_changes.append(commit_title)
        if is_dataloss:
            self.dataloss_changes.append(commit_title)
        if is_breaking:
            self.breaking_changes.append(commit_title)

    def open_temp_file(self, initial_message: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
            tf.write(initial_message)
            tf.flush()
            call(["vim", "+set backupcopy=yes", tf.name])
            tf.seek(0)
            return tf.read().decode("utf-8").strip()

    def update_the_tag(self) -> None:
        initial_message = (
            f"# Type your desired tag below here (max 16 chars):\n{self.release_tag}"
        ).encode("utf-8")
        edited_message = self.open_temp_file(initial_message)
        self.release_tag = (
            edited_message.split("\n")[1][:16]
            if len(edited_message.split("\n")) > 1
            else self.get_default_tag()
        )

    def update_the_title(self) -> None:
        initial_message = (
            f"# Type your desired title below here (max 80 chars):\n{self.release_title}"
        ).encode("utf-8")
        edited_message = self.open_temp_file(initial_message)
        self.release_title = (
            edited_message.split("\n")[1][:80]
            if len(edited_message.split("\n")) > 1
            else "Awesome Title"
        )

    def update_the_description(self) -> None:
        initial_message = (
            f"# Type your desired description below here:\n{self.release_description}"
        ).encode("utf-8")
        edited_message = self.open_temp_file(initial_message)
        self.release_description = (
            "\n".join(edited_message.split("\n")[1:])
            if len(edited_message.split("\n")) > 1
            else "TBD"
        )

    def update_the_breaking_changes_list(self) -> None:
        stream = StringIO()
        yaml.dump(self.breaking_changes, stream)
        initial_message = (
            "# Type your updated breaking changes list below here as a yaml/json list:\n"
            + stream.getvalue()
        ).encode("utf-8")
        edited_message = self.open_temp_file(initial_message)
        try:
            new_list = yaml.load(edited_message)
            if isinstance(new_list, list):
                self.breaking_changes = new_list
        except YAMLError:
            pass

    def update_the_downtime_changes_list(self) -> None:
        stream = StringIO()
        yaml.dump(self.downtime_changes, stream)
        initial_message = (
            "# Type your updated downtime changes list below here as a yaml/json list:\n"
            + stream.getvalue()
        ).encode("utf-8")
        edited_message = self.open_temp_file(initial_message)
        try:
            new_list = yaml.load(edited_message)
            if isinstance(new_list, list):
                self.downtime_changes = new_list
        except YAMLError:
            pass

    def update_the_dataloss_changes_list(self) -> None:
        stream = StringIO()
        yaml.dump(self.dataloss_changes, stream)
        initial_message = (
            "# Type your updated data loss changes list below here as a yaml/json list:\n"
            + stream.getvalue()
        ).encode("utf-8")
        edited_message = self.open_temp_file(initial_message)
        try:
            new_list = yaml.load(edited_message)
            if isinstance(new_list, list):
                self.dataloss_changes = new_list
        except YAMLError:
            pass

    def move_up(self) -> None:
        self.index -= 1
        if self.index < 0:
            self.index = len(self.options) - 1

    def move_down(self) -> None:
        self.index += 1
        if self.index >= len(self.options):
            self.index = 0

    @classmethod
    def verify_github_token(cls, token: str) -> bool:
        github_client = Github(token)
        try:
            github_client.get_user().name
            return True
        except GithubException:
            return False

    def config_curses(self) -> None:
        try:
            # use the default colors of the terminal
            curses.use_default_colors()
            for i in range(0, curses.COLORS):
                curses.init_pair(i + 1, i, -1)
            # hide the cursor
            curses.curs_set(0)
        except Exception:
            # Curses failed to initialize color support, eg. when TERM=vt100
            curses.initscr()

    def render_commit_info(self, index: int) -> None:
        if self.screen is None:
            raise Exception("Screen not set")
        self.screen.clear()
        x, y = 1, 1  # start point
        max_y, max_x = self.screen.getmaxyx()
        # max_rows = max_y - y  # TODO: handle overflow
        commit = self.commits_since_last_release[index]
        message_blocks = commit.commit.message.split("\n")
        cur_str = "Commit Title: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y, x, message_blocks[0], max_x - 2, curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Commit Author: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            commit.commit.author.name,
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Commit Date: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            str(commit.commit.author.date),
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Commit Url: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y, x, commit.commit.html_url, max_x - 2, curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        pull_requests: List[PullRequest] = [x for x in commit.get_pulls()]  # type: ignore
        if len(pull_requests) > 0:
            pull_request = pull_requests[0]
            cur_str = "Commit Pull Request: "
            self.screen.addnstr(y, x, cur_str, max_x - 2)
            x += len(cur_str)
            self.screen.addnstr(
                y,
                x,
                pull_request.html_url,
                max_x - 2,
                curses.A_BOLD | curses.color_pair(6),
            )
            x = 1
            y += 1

        cur_str = "Commit Message:\n"
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        y += 1
        for block in message_blocks[1:]:
            for i in range(0, len(block), max_x - 2):
                self.screen.addnstr(
                    y, x, block[i : max_x - 2], max_x - 2, curses.A_BOLD,
                )
                y += 1

        if len(pull_requests) > 0:
            pull_request = pull_requests[0]
            body = pull_request.body
            cur_str = "Pull Request Body: "
            self.screen.addnstr(y, x, cur_str, max_x - 2)
            y += 1
            for block in body.split("\n"):
                for i in range(0, len(block), max_x - 2):
                    self.screen.addnstr(
                        y, x, block[i : max_x - 2], max_x - 2, curses.A_BOLD,
                    )
                    y += 1

        cur_str = "Hit Enter to go back to main page."
        self.screen.addnstr(y, x, cur_str, max_x - 2, curses.color_pair(3))
        y += 1

        self.screen.refresh()

    def commit_info_loop(self, index: int) -> None:
        if self.screen is None:
            raise Exception("Screen not set")
        while True:
            self.render_commit_info(index)
            c = self.screen.getch()
            if c in KEYS_ENTER:
                break

    def finalize_draft_loop(self) -> None:
        if self.screen is None:
            raise Exception("Screen not set")
        while True:
            self.render_finalize_draft()
            c = self.screen.getch()
            if c in KEYS_ENTER:
                new_release = self.submit_draft()
                curses.endwin()
                print(
                    "Congratulations on the new draft release, you can find it in this link: ",
                    new_release.html_url,
                )
                exit(0)
            break

    def submit_draft(self) -> GitRelease:
        latest_commit = self.commits_since_last_release[0]
        return self.opta_repo.create_git_tag_and_release(
            tag=self.release_tag,
            tag_message="See release notes",
            release_name=self.release_title,
            release_message=self.compile_release_body(),
            draft=True,
            object=latest_commit.sha,
            type="commit",
        )

    def render_finalize_draft(self) -> None:
        if self.screen is None:
            raise Exception("Screen not set")
        self.screen.clear()
        x, y = 1, 1  # start point
        max_y, max_x = self.screen.getmaxyx()
        # max_rows = max_y - y  # TODO: handle overflow

        cur_str = (
            "OK, let's go over this one more time before we create the draft release: "
        )
        self.screen.addnstr(y, x, cur_str, max_x - 2, curses.color_pair(3))
        y += 1

        cur_str = "Release to be made: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y, x, self.release_tag, max_x - 2, curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Release title to be made: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y, x, self.release_title, max_x - 2, curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 2

        latest_commit = self.commits_since_last_release[0]
        cur_str = "Name of commit to bind: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            latest_commit.commit.message.split("\n")[0],
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 2

        cur_str = "Sha of commit to bind: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            latest_commit.commit.sha,
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 2

        cur_str = "Body of release (release notes): "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        y += 1
        release_body = self.compile_release_body()

        for block in release_body.split("\n"):
            for i in range(0, len(block), max_x - 2):
                self.screen.addnstr(
                    y, x, block[i : max_x - 2], max_x - 2, curses.A_BOLD,
                )
                y += 1
            if len(block) == 0:
                y += 1

    def compile_release_body(self) -> str:
        commit_list_lines = "\n".join([f"- {x}" for x in self.commit_titles])
        breaking_changes_lines = "\n".join([f"- {x}" for x in self.breaking_changes])
        downtime_changes_lines = "\n".join([f"- {x}" for x in self.downtime_changes])
        dataloss_changes_lines = "\n".join([f"- {x}" for x in self.downtime_changes])
        return RELEASE_TEMPLATE.format(
            description=self.release_description,
            commit_list_lines=commit_list_lines,
            breaking_changes_lines=breaking_changes_lines,
            downtime_changes_lines=downtime_changes_lines,
            dataloss_changes_lines=dataloss_changes_lines,
        )

    def run_loop(self) -> None:
        if self.screen is None:
            raise Exception("Screen not set")
        while True:
            self.render_main_page()
            c = self.screen.getch()
            if c in KEYS_UP:
                self.move_up()
            elif c in KEYS_DOWN:
                self.move_down()
            elif c in KEYS_ENTER:
                curses.endwin()
                num_commits = len(self.commits_since_last_release)
                if self.index in range(num_commits):
                    self.commit_info_loop(self.index)
                elif self.index == num_commits:
                    self.update_the_tag()
                elif self.index == num_commits + 1:
                    self.update_the_title()
                elif self.index == num_commits + 2:
                    self.update_the_description()
                elif self.index == num_commits + 3:
                    self.update_the_breaking_changes_list()
                elif self.index == num_commits + 4:
                    self.update_the_downtime_changes_list()
                elif self.index == num_commits + 5:
                    self.update_the_dataloss_changes_list()
                elif self.index == num_commits + 6:
                    self.finalize_draft_loop()
                elif self.index == num_commits + 7:
                    exit(0)
                else:
                    raise Exception(
                        f"Invalid index {self.index} for options {self.options}"
                    )
                self.refresh_options()

    def _start(self, screen: window) -> None:
        self.screen = screen
        self.config_curses()
        try:
            return self.run_loop()
        except KeyboardInterrupt:
            exit(1)

    def start(self) -> None:
        if len(self.commits_since_last_release) == 0:
            print(
                f"{attr('orange_4b') + attr('bold')}WARNING{attr(0)}: looks like there has been zero commits since the "
                "last release. Exiting now"
            )
            exit(0)
        return curses.wrapper(self._start)

    def render_main_page(self) -> None:
        if self.screen is None:
            raise Exception("Screen not set")
        self.screen.clear()
        x, y = 1, 1  # start point
        max_y, max_x = self.screen.getmaxyx()
        # max_rows = max_y - y  # TODO: handle overflow
        cur_str = "Last release was: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            self.latest_release.title,
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Last tag was: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            self.latest_release.tag_name,
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 2

        cur_str = f"Found the following {len(self.commits_since_last_release)} commits since last release:\n"
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        y += 1

        for title in self.commit_titles:
            self.screen.addnstr(y, x, f"- {title}", max_x - 2, curses.A_BOLD)
            y += 1
        y += 1

        cur_str = "Current working tag: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y, x, self.release_tag, max_x - 2, curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Current working title: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y, x, self.release_title, max_x - 2, curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Current working description: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        y += 1

        for i in range(0, len(self.release_description), max_x - 2):
            self.screen.addnstr(
                y,
                x,
                self.release_description[i : max_x - 2],
                max_x - 2,
                curses.A_BOLD | curses.color_pair(6),
            )
            y += 1

        cur_str = "Currently identified breaking changes: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        if len(self.breaking_changes) == 0:
            self.screen.addnstr(y, x + len(cur_str), "[ ]", max_x - 2)
        y += 1
        for cur_str in self.breaking_changes:
            self.screen.addnstr(y, x, "- ", max_x - 2)
            self.screen.addnstr(y, x + 2, cur_str, max_x - 2, curses.color_pair(4))
            y += 1

        cur_str = "Currently identified downtime changes: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        if len(self.downtime_changes) == 0:
            self.screen.addnstr(y, x + len(cur_str), "[ ]", max_x - 2)
        y += 1
        for cur_str in self.downtime_changes:
            self.screen.addnstr(y, x, "- ", max_x - 2)
            self.screen.addnstr(y, x + 2, cur_str, max_x - 2, curses.color_pair(4))
            y += 1

        cur_str = "Currently identified data loss changes: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        if len(self.dataloss_changes) == 0:
            self.screen.addnstr(y, x + len(cur_str), "[ ]", max_x - 2)
        y += 1
        for cur_str in self.dataloss_changes:
            self.screen.addnstr(y, x, "- ", max_x - 2)
            self.screen.addnstr(y, x + 2, cur_str, max_x - 2, curses.color_pair(4))
            y += 1
        y += 1

        cur_str = "Please let us know what action you wish to take down below! "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        y += 1

        for index, option in enumerate(self.options):
            prefix = "* " if index == self.index else "  "
            cur_str = prefix + option

            self.screen.addnstr(y, x, cur_str[: max_x - 3], max_x - 2)
            y += 1

        self.screen.refresh()


if __name__ == "__main__":
    print(f"{fg('green')}Buckle up buckaroos!{attr(0)}")
    ReleaseHelper().start()
