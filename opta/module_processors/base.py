from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class ModuleProcessor:
    def __init__(self, module: "Module", layer: "Layer") -> None:
        self.layer = layer
        self.module = module

    def process(self, block_idx: int) -> None:
        self.module.data["env_name"] = self.layer.get_env()
        self.module.data["layer_name"] = self.layer.name
        self.module.data["module_name"] = self.module.name


class K8sModuleProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        self.iam = boto3.client("iam")
        providers = layer.gen_providers(0)
        region = providers["terraform"]["backend"]["s3"]["region"]
        self.eks = boto3.client("eks", config=Config(region_name=region))
        super(K8sModuleProcessor, self).__init__(module, layer)

    def process(self, block_idx: int) -> None:
        eks_cluster = self.eks.describe_cluster(name=f"opta-{self.layer.get_env()}")
        oidc_url = eks_cluster["cluster"]["identity"]["oidc"]["issuer"].replace(
            "https://", ""
        )
        oid_provider_list = self.iam.list_open_id_connect_providers()[
            "OpenIDConnectProviderList"
        ]
        for oidc_provider_data in oid_provider_list:
            arn = oidc_provider_data["Arn"]
            full_data = self.iam.get_open_id_connect_provider(
                OpenIDConnectProviderArn=arn
            )
            if full_data["Url"] == oidc_url:
                self.module.data["openid_provider_url"] = oidc_url
                self.module.data["openid_provider_arn"] = arn
                super(K8sModuleProcessor, self).process(block_idx)
                return
        raise Exception("Did not find identity provider for K8s cluster")
