from subprocess import CalledProcessError  # nosec
from typing import FrozenSet, List, Optional

import opta.constants as constants
from opta.exceptions import UserErrors
from opta.nice_subprocess import nice_run
from opta.utils import json
from opta.utils.dependencies import ensure_installed


class Helm:
    @staticmethod
    def get_required_path_executables() -> FrozenSet[str]:
        return frozenset({"helm"})

    @staticmethod
    def validate_helm_installed() -> None:
        ensure_installed("helm")

    @classmethod
    def rollback_helm(
        cls, kube_context: str, release: str, namespace: str, revision: str = ""
    ) -> None:
        cls.validate_helm_installed()
        try:
            if revision == "1":
                nice_run(
                    [
                        "helm",
                        "uninstall",
                        release,
                        "--kube-context",
                        kube_context,
                        "--kubeconfig",
                        constants.GENERATED_KUBE_CONFIG or constants.DEFAULT_KUBECONFIG,
                        "--namespace",
                        namespace,
                    ],
                    check=True,
                )
            else:
                nice_run(
                    [
                        "helm",
                        "rollback",
                        release,
                        revision,
                        "--kube-context",
                        kube_context,
                        "--kubeconfig",
                        constants.GENERATED_KUBE_CONFIG or constants.DEFAULT_KUBECONFIG,
                        "--namespace",
                        namespace,
                    ],
                    check=True,
                )
        except CalledProcessError as e:
            raise UserErrors(
                f"Helm was unable to rollback the release: {release}.\n"
                "Following error was raised by Helm:\n"
                f"{e.stderr}"
            )
        except Exception as e:
            raise e

    @classmethod
    def get_helm_list(cls, kube_context: str, namespace: Optional[str] = None, release: Optional[str] = None, status: Optional[str] = None) -> List:  # type: ignore # nosec
        """
        Returns a list of helm releases.
        The releases can be filtered by namespace, release name and status.
        """
        cls.validate_helm_installed()
        namespaces: List[str] = []
        if namespace is not None:
            namespaces.append("--namespace")
            namespaces.append(str(namespace))
        else:
            namespaces.append("--all-namespaces")

        try:
            helm_list_process = nice_run(
                [
                    "helm",
                    "list",
                    "--all",
                    "--kube-context",
                    kube_context,
                    "--kubeconfig",
                    constants.GENERATED_KUBE_CONFIG or constants.DEFAULT_KUBECONFIG,
                    *namespaces,
                    "-o",
                    "json",
                ],
                capture_output=True,
                check=True,
            )
        except CalledProcessError as e:
            raise UserErrors(f"Error: {e.stderr}")
        except Exception as e:
            raise e

        helm_list = json.loads(helm_list_process.stdout)

        if release is not None:
            helm_list = [
                helm_release
                for helm_release in helm_list
                if helm_release["name"] == release
            ]
        if status is not None:
            helm_list = [
                helm_release
                for helm_release in helm_list
                if helm_release["status"] == status
            ]
        return helm_list
