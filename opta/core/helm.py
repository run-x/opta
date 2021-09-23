import json
from subprocess import CalledProcessError
from typing import List

from opta.exceptions import UserErrors
from opta.nice_subprocess import nice_run
from opta.utils import is_tool

HELM_INSTALL_URL = "https://helm.sh/docs/intro/install/"


def helm_check() -> None:
    if not is_tool("helm"):
        raise UserErrors(
            f"Please visit this link to install helm first: {HELM_INSTALL_URL}"
        )


class Helm:
    @classmethod
    def rollback_helm(cls, release: str, namespace: str, revision: str = "") -> None:
        helm_check()
        try:
            if revision == "1":
                nice_run(
                    ["helm", "uninstall", release, "--namespace", namespace], check=True
                )
            else:
                nice_run(
                    ["helm", "rollback", release, revision, "--namespace", namespace],
                    check=True,
                )
        except CalledProcessError as e:
            raise UserErrors(
                f"Helm was unable to rollback the release: {release}.\n"
                "Following error was raised by Helm:\n"
                f"{e.stderr.decode('UTF-8')}"
            )
        except Exception as e:
            raise e

    @classmethod
    def get_helm_list(cls, **kwargs) -> List:  # type: ignore # nosec
        helm_check()
        namespaces: List[str] = []
        if kwargs.get("namespace") is not None:
            namespaces.append("--namespace")
            namespaces.append(str(kwargs.get("namespace")))
        else:
            namespaces.append("--all-namespaces")

        try:
            helm_list_process = nice_run(
                ["helm", "list", "--all", *namespaces, "-o", "json"],
                capture_output=True,
                check=True,
            )
        except CalledProcessError as e:
            raise UserErrors(f"Error: {e.stderr.decode('UTF-8')}")
        except Exception as e:
            raise e

        helm_list = json.loads(helm_list_process.stdout.decode("UTF-8"))

        if kwargs.get("release"):
            helm_list = [
                helm_release
                for helm_release in helm_list
                if helm_release["name"] == kwargs.get("release")
            ]
        if kwargs.get("status"):
            helm_list = [
                helm_release
                for helm_release in helm_list
                if helm_release["status"] == kwargs.get("status")
            ]
        return helm_list
