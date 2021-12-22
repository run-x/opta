import os

from pytest_mock import MockFixture

from modules.cloudfront_distribution.cloudfront_distribution import (
    CloudfrontDistributionProcessor,
)
from opta.layer import Layer


class TestCloudfrontDstributionProcessor:
    def test_all_good(self, mocker: MockFixture) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        cloudfront_module = layer.get_module("cloudfront", idx)
        assert cloudfront_module is not None
        CloudfrontDistributionProcessor(cloudfront_module, layer).process(idx)
        assert cloudfront_module.data["bucket_name"] == "${{module.bucket1.bucket_id}}"
        assert (
            cloudfront_module.data["origin_access_identity_path"]
            == "${{module.bucket1.cloudfront_read_path}}"
        )
