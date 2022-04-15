#!/usr/bin/env python
import curses
import os
import re
import tempfile
from curses import window
from io import StringIO
from subprocess import call
from typing import List, Optional, Tuple

import click
import semver
from colored import attr, fg
from github import Github, GithubException
from github.Commit import Commit
from github.GitRef import GitRef
from github.GitRelease import GitRelease
from github.PullRequest import PullRequest
from github.Repository import Repository

from opta.utils import yaml
from opta.utils.yaml import YAMLError

KEYS_ENTER = (curses.KEY_ENTER, ord("\n"), ord("\r"))
KEYS_UP = (curses.KEY_UP, ord("k"))
KEYS_PANE_TOGGLE = (curses.KEY_LEFT, curses.KEY_RIGHT)
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


class OptaPane:
    def __init__(self, sub_window: window):
        self.screen = sub_window
        self.border = False

    def toggle_border(self) -> None:
        self.border = not self.border

    def handle_enter(self) -> None:
        pass

    def move_up(self) -> None:
        pass

    def move_down(self) -> None:
        pass

    def get_maxyx(self) -> Tuple[int, int]:
        max_y, max_x = self.screen.getmaxyx()
        return max_y - 2, max_x - 2

    def get_minyx(self) -> Tuple[int, int]:
        return 2, 2

    def render(self) -> None:
        if self.border:
            self.screen.box()
        self.screen.refresh()


class StatusPane(OptaPane):
    def __init__(
        self,
        sub_window: window,
        github_client: Github,
        latest_release: GitRelease,
        commits_since_last_release: List[Commit],
    ) -> None:
        self.github_client = github_client
        self.opta_repo = self.github_client.get_repo("run-x/opta")
        self.index = 0
        self.latest_release = latest_release
        self.commits_since_last_release = commits_since_last_release
        self.commit_titles = [
            commit.commit.message.split("\n")[0]
            for commit in self.commits_since_last_release
        ]
        super(StatusPane, self).__init__(sub_window=sub_window)

    def move_up(self) -> None:
        self.index -= 1
        if self.index < 0:
            self.index = len(self.commit_titles) - 1

    def move_down(self) -> None:
        self.index += 1
        if self.index >= len(self.commit_titles):
            self.index = 0

    def handle_enter(self) -> None:
        self.commit_info_loop(self.index)

    def commit_info_loop(self, index: int) -> None:
        commit_info_pane = CommitInfoPane(
            cur_window=self.screen, commit=self.commits_since_last_release[index]
        )
        commit_info_pane.toggle_border()
        while True:
            commit_info_pane.render()
            c = self.screen.getch()
            if c in KEYS_ENTER:
                break

    def render(self) -> None:
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

        for index, title in enumerate(self.commit_titles):
            prefix = "* " if index == self.index else "  "
            self.screen.addnstr(y, x, prefix, max_x - 2, curses.A_BOLD)
            x += 2
            for i in range(0, len(title), max_x - 4):
                self.screen.addnstr(
                    y, x, title[i : max_x - 2], max_x - 2, curses.A_BOLD,
                )
                y += 1
            x = 1
        y += 1

        super(StatusPane, self).render()


class PlanningPane(OptaPane):
    def __init__(
        self,
        sub_window: window,
        github_client: Github,
        latest_release: GitRelease,
        commits_since_last_release: List[Commit],
    ) -> None:
        self.github_client = github_client
        self.opta_repo = self.github_client.get_repo("run-x/opta")
        self.latest_release = latest_release
        self.index = 0
        self.release_title = "Awesome Title"
        self.release_description = "TBD"
        self.breaking_changes: List[str] = []
        self.downtime_changes: List[str] = []
        self.dataloss_changes: List[str] = []
        self.options: List[str] = []
        self.release_tag = self.get_default_tag()
        self.commits_since_last_release = commits_since_last_release
        for commit in self.commits_since_last_release:
            self.fill_in_commit_defaults(commit)
        self.commit_titles = [
            commit.commit.message.split("\n")[0]
            for commit in self.commits_since_last_release
        ]
        self.refresh_options()
        super(PlanningPane, self).__init__(sub_window=sub_window)

    def fill_in_commit_defaults(self, commit: Commit) -> None:
        pull_requests: List[PullRequest] = [x for x in commit.get_pulls()]  # type: ignore
        is_breaking = True
        is_downtime = True
        is_dataloss = True
        commit_title = commit.commit.message.split("\n")[0]

        if len(pull_requests) > 0:
            pull_request = pull_requests[-1]
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

    def get_default_tag(self) -> str:
        try:
            return "v" + str(
                semver.VersionInfo.parse(
                    self.latest_release.tag_name.strip("v")
                ).bump_minor()
            )
        except Exception:
            return "WIP"

    def move_up(self) -> None:
        self.index -= 1
        if self.index < 0:
            self.index = len(self.options) - 1

    def move_down(self) -> None:
        self.index += 1
        if self.index >= len(self.options):
            self.index = 0

    def handle_enter(self) -> None:
        if self.index == 0:
            self.update_the_tag()
        elif self.index == 1:
            self.update_the_title()
        elif self.index == 2:
            self.update_the_description()
        elif self.index == 3:
            self.update_the_breaking_changes_list()
        elif self.index == 4:
            self.update_the_downtime_changes_list()
        elif self.index == 5:
            self.update_the_dataloss_changes_list()
        elif self.index == 6:
            self.finalize_draft_loop()

    def finalize_draft_loop(self) -> None:
        finalize_draft_pane = FinalizeDraftPane(
            cur_window=self.screen,
            opta_repo=self.opta_repo,
            dataloss_changes=self.dataloss_changes,
            downtime_changes=self.downtime_changes,
            breaking_changes=self.breaking_changes,
            release_tag=self.release_tag,
            release_title=self.release_title,
            release_description=self.release_description,
            latest_commit=self.commits_since_last_release[0],
            commit_titles=self.commit_titles,
        )
        while True:
            finalize_draft_pane.render()
            c = self.screen.getch()
            if c in KEYS_ENTER:
                new_release = finalize_draft_pane.submit_draft()
                curses.endwin()
                print(
                    "Congratulations on the new draft release, you can find it in this link: ",
                    new_release.html_url,
                )
                exit(0)
            break

    def render(self) -> None:
        self.screen.clear()
        self.refresh_options()
        x, y = 1, 1  # start point
        max_y, max_x = self.screen.getmaxyx()

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

        super(PlanningPane, self).render()

    def refresh_options(self) -> None:
        options = []
        options.append(f"I want to change the tag from {self.release_tag}")
        options.append(f"I want to update the release title from {self.release_title}")
        options.append("I want to update the release description")
        options.append("I want to update the breaking changes list")
        options.append("I want to update the downtime changes list")
        options.append("I want to udpate the data loss changes list")
        options.append("I want to finalize the draft")
        self.options = options

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


class CommitInfoPane(OptaPane):
    def __init__(self, cur_window: window, commit: Commit) -> None:
        self.commit = commit
        super(CommitInfoPane, self).__init__(sub_window=cur_window)

    def render(self) -> None:
        if self.screen is None:
            raise Exception("Screen not set")
        self.screen.clear()
        x, y = 1, 1  # start point
        max_y, max_x = self.screen.getmaxyx()
        message_blocks = self.commit.commit.message.split("\n")
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
            self.commit.commit.author.name,
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
            str(self.commit.commit.author.date),
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        cur_str = "Commit Url: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            self.commit.commit.html_url,
            max_x - 2,
            curses.A_BOLD | curses.color_pair(6),
        )
        x = 1
        y += 1

        pull_requests: List[PullRequest] = [x for x in self.commit.get_pulls()]  # type: ignore
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

        super(CommitInfoPane, self).render()


class FinalizeDraftPane(OptaPane):
    def __init__(
        self,
        cur_window: window,
        opta_repo: Repository,
        commit_titles: List[str],
        release_tag: str,
        release_title: str,
        latest_commit: Commit,
        breaking_changes: List[str],
        downtime_changes: List[str],
        dataloss_changes: List[str],
        release_description: str,
    ) -> None:
        self.opta_repo = opta_repo
        self.commit_titles = commit_titles
        self.release_tag = release_tag
        self.release_title = release_title
        self.latest_commit = latest_commit
        self.breaking_changes = breaking_changes
        self.downtime_changes = downtime_changes
        self.dataloss_changes = dataloss_changes
        self.release_description = release_description
        super(FinalizeDraftPane, self).__init__(cur_window)

    def render(self) -> None:
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

        cur_str = "Name of commit to bind: "
        self.screen.addnstr(y, x, cur_str, max_x - 2)
        x += len(cur_str)
        self.screen.addnstr(
            y,
            x,
            self.latest_commit.commit.message.split("\n")[0],
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
            self.latest_commit.commit.sha,
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
        super(FinalizeDraftPane, self).render()

    def compile_release_body(self) -> str:
        commit_list_lines = "\n".join([f"- {x}" for x in self.commit_titles])
        breaking_changes_lines = "\n".join([f"- {x}" for x in self.breaking_changes])
        downtime_changes_lines = "\n".join([f"- {x}" for x in self.downtime_changes])
        dataloss_changes_lines = "\n".join([f"- {x}" for x in self.dataloss_changes])
        return RELEASE_TEMPLATE.format(
            description=self.release_description,
            commit_list_lines=commit_list_lines,
            breaking_changes_lines=breaking_changes_lines,
            downtime_changes_lines=downtime_changes_lines,
            dataloss_changes_lines=dataloss_changes_lines,
        )

    def submit_draft(self) -> GitRelease:
        return self.opta_repo.create_git_tag_and_release(
            tag=self.release_tag,
            tag_message="See release notes",
            release_name=self.release_title,
            release_message=self.compile_release_body(),
            draft=True,
            object=self.latest_commit.sha,
            type="commit",
        )


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
        self.latest_release = self.opta_repo.get_latest_release()
        self.current_pane_index = 0

        tag_ref: GitRef = self.opta_repo.get_git_matching_refs(
            "tags/" + self.latest_release.tag_name
        )[0]
        commit_sha = tag_ref.object.sha
        self.last_release_commit = self.opta_repo.get_commit(commit_sha)
        self.commits_since_last_release = [
            x
            for x in self.opta_repo.get_commits(
                since=self.last_release_commit.commit.author.date, sha="dev"
            )
        ][:-1]

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

    def run_loop(self) -> None:
        if self.screen is None:
            raise Exception("Screen not set")

        x, y = 0, 0  # start point
        max_y, max_x = self.screen.getmaxyx()

        status_pane_window = self.screen.subwin(max_y - 1, int(max_x / 2), y, x)
        status_pane = StatusPane(
            sub_window=status_pane_window,
            github_client=self.github_client,
            latest_release=self.latest_release,
            commits_since_last_release=self.commits_since_last_release,
        )
        planning_pane_window = self.screen.subwin(
            max_y - 1, int(max_x / 2) - 1, y, int(max_x / 2)
        )
        planning_pane = PlanningPane(
            sub_window=planning_pane_window,
            github_client=self.github_client,
            latest_release=self.latest_release,
            commits_since_last_release=self.commits_since_last_release,
        )
        current_pane: OptaPane = status_pane
        current_pane.toggle_border()

        while True:
            status_pane.render()
            planning_pane.render()
            c = self.screen.getch()
            if c in KEYS_UP:
                current_pane.move_up()
            elif c in KEYS_DOWN:
                current_pane.move_down()
            elif c in KEYS_PANE_TOGGLE:
                current_pane.toggle_border()
                if current_pane == status_pane:
                    current_pane = planning_pane
                else:
                    current_pane = status_pane
                current_pane.toggle_border()
            elif c in KEYS_ENTER:
                curses.endwin()
                current_pane.handle_enter()

    def _start(self, screen: window) -> None:
        self.screen = screen
        self.config_curses()
        try:
            return self.run_loop()
        except KeyboardInterrupt:
            exit(0)

    def start(self) -> None:
        if len(self.commits_since_last_release) == 0:
            print(
                f"{attr('orange_4b') + attr('bold')}WARNING{attr(0)}: looks like there has been zero commits since the "
                "last release. Exiting now"
            )
            exit(0)
        return curses.wrapper(self._start)


if __name__ == "__main__":
    print(f"{fg('green')}Buckle up buckaroos!{attr(0)}")
    ReleaseHelper().start()
