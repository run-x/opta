from tempfile import TemporaryDirectory

from opta.core.cloud_provider import CloudProvider
from opta.layer2 import Layer

class TerraformGenerator:
    def __init__(self, cloud: CloudProvider):
        self._work_dir: TemporaryDirectory = None
        self.cloud = cloud

    @property
    def work_dir(self):
        if not self._work_dir:
            self._work_dir = TemporaryDirectory()

        return self._work_dir.name

    def generate(self, layer: Layer):
        tf_config = self.cloud.terraform_provider_config(self.layer)


    def _generate_provider(self):
        data = {}
        providers = {
            "aws": []
        }
