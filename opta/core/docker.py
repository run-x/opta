import os

import docker
from docker.errors import APIError

DOCKER_PUSH_STATUS_PREPARING = "Preparing"
DOCKER_PUSH_STATUS_PUSHING = "Pushing"
DOCKER_PUSH_STATUS_WAITING = "Waiting"


VALID_DOCKER_PUSH_STATUS = [
    DOCKER_PUSH_STATUS_PREPARING,
    DOCKER_PUSH_STATUS_PUSHING,
    DOCKER_PUSH_STATUS_WAITING,
]


class Docker:
    def __init__(self, username: str, password: str, registry: str):
        self.docker_client = docker.from_env()
        self.registry = registry
        try:
            self.__login__(username, password, registry)
        except APIError as e:
            raise Exception(e.__str__())

    @staticmethod
    def _remove_docker_config() -> None:
        os.remove(os.path.join("~", ".docker", "config.json"))

    def __login__(self, username: str, password: str, registry: str) -> None:
        self._remove_docker_config()
        _ = self.docker_client.login(
            username=username, password=password, registry=registry
        )

    def tag_image(self, image: str, tag: str = "latest") -> bool:
        try:
            tagged = self.docker_client.api.tag(image, self.registry, tag=tag)
        except APIError as e:
            raise Exception(e.__str__())
        return tagged

    def push_image(self, tag: str = "latest") -> None:
        self.push_stream: dict = {}
        try:
            for stream_element in self.docker_client.api.push(
                self.registry, tag=tag, stream=True, decode=True
            ):
                print(stream_element)
        except APIError as e:
            raise Exception(e.__str__())
        finally:
            self.push_stream = {}

    # def _pretty_print_docker_push(self, stream_element: dict) -> None:
    #     if stream_element.__contains__("error_details") and stream_element.__contains__(
    #         "error"
    #     ):
    #         raise Exception(stream_element.get("error"))
    #
    #     pretty_print_stream = ""
    #     id = stream_element.get("id", "")
    #     pretty_print = (
    #         f"{stream_element.get('status', '')} \t {stream_element.get('progress', '')}"
    #     )
    #     self.push_stream[id] = f"{id}:\t{pretty_print}" if id else pretty_print
    #
    #     for _, value in self.push_stream.items():
    #         pretty_print_stream += value
    #
    #     print(f"{pretty_print_stream}", end="\r")
