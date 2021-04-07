from typing import TYPE_CHECKING, List, Optional, Tuple

import boto3
from botocore.config import Config
from click import prompt
from colored import attr, fg
from mypy_boto3_ssm.client import SSMClient
from OpenSSL.crypto import (
    FILETYPE_PEM,
    X509,
    Error,
    PKey,
    dump_publickey,
    load_certificate,
    load_privatekey,
)

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module

PRIVATE_KEY_FILE_NAME = "dns-private-key.pem"
CERTIFICATE_CHAIN_FILE_NAME = "dns-certificate-chain.pem"
CERTIFICATE_BODY_FILE_NAME = "dns-certificate-body.pem"


class AwsDnsProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(AwsDnsProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        if self.module.data["upload_cert"]:
            ssm_client: SSMClient = boto3.client("ssm", config=Config(region_name=region))
            parameters = ssm_client.get_parameters_by_path(
                Path=f"/opta-{self.layer.get_env()}", Recursive=True
            ).get("Parameters", [])
            parameter_names = list(map(lambda x: x["Name"], parameters))
            files_found = False
            private_key_ssm_path = f"/opta-{self.layer.get_env()}/{PRIVATE_KEY_FILE_NAME}"
            cert_body_ssm_path = (
                f"/opta-{self.layer.get_env()}/{CERTIFICATE_BODY_FILE_NAME}"
            )
            cert_chain_ssm_path = (
                f"/opta-{self.layer.get_env()}/{CERTIFICATE_CHAIN_FILE_NAME}"
            )
            if {private_key_ssm_path, cert_body_ssm_path}.issubset(set(parameter_names)):
                logger.info("SSL files found in cloud")
                files_found = True
            if cert_chain_ssm_path in parameter_names:
                self.module.data["cert_chain_included"] = True
            force_update = self.module.data.get("force_update", False)
            if (force_update or not files_found) and not self.module.data.get(
                "_updated_already", False
            ):
                logger.info(
                    f"{fg(5)}{attr(1)}You have indicated that you wish to pass in your own ssl certificate and the files have not been "
                    "found on the cloud or you have specified an update must be forced. "
                    "This is not the typically recommended option as the dns delegation way "
                    "includes certificate refreshing so if you don't do this you will need to periodically force a new "
                    f"update. Sometimes this can not be helped, which brings us here.{attr(0)}"
                )
                matching_cert_and_keys = False
                while not matching_cert_and_keys:
                    private_key_obj, private_key_str = self.fetch_private_key()
                    cert_obj, cert_str = self.fetch_cert_body()
                    cert_pub = dump_publickey(FILETYPE_PEM, cert_obj.get_pubkey())
                    key_pub = dump_publickey(FILETYPE_PEM, private_key_obj)
                    if cert_pub != key_pub:
                        logger.warn(
                            "Certificate private key does not match inputted private key, try again"
                        )
                        continue
                    cert_chain_obj, cert_chain_str = self.fetch_cert_chain()
                    # TODO: add cert chain validation and full chain validation against trusted CA
                    domains_list = self.get_subject_alternative_names(cert_obj)
                    if self.module.data["domain"] not in domains_list:
                        raise UserErrors(
                            f"You provided a domain of {self.module.data['domain']} but the cert is only for domains {domains_list}"
                        )
                    matching_cert_and_keys = True
                if cert_chain_str:
                    ssm_client.put_parameter(
                        Name=cert_chain_ssm_path,
                        Value=cert_chain_str,
                        Type="SecureString",
                        Overwrite=True,
                    )
                    self.module.data["cert_chain_included"] = True
                else:
                    ssm_client.delete_parameter(Name=cert_chain_ssm_path,)
                ssm_client.put_parameter(
                    Name=private_key_ssm_path,
                    Value=private_key_str,
                    Type="SecureString",
                    Overwrite=True,
                )
                ssm_client.put_parameter(
                    Name=cert_body_ssm_path,
                    Value=cert_str,
                    Type="SecureString",
                    Overwrite=True,
                )
                logger.info(
                    "certificate files uploaded securely to parameter store for future consumption"
                )
                self.module.data["_updated_already"] = True
        super(AwsDnsProcessor, self).process(module_idx)

    def fetch_private_key(self) -> Tuple[PKey, str]:
        while True:
            privkey_path = prompt(
                "Please enter the full path to the private key pem file found locally. This is typically called privkey.pem or something like that.",
                type=str,
            )
            try:
                with open(privkey_path, "r") as f:
                    privkey = f.read()
            except FileNotFoundError:
                logger.warn(
                    f"Could not find private key with path {privkey_path}. Pls try again"
                )
                continue
            try:
                private_key_obj = load_privatekey(FILETYPE_PEM, privkey)
                return private_key_obj, privkey
            except Error:
                logger.warn("private key is not correct pem private key")
                continue

    def fetch_cert_body(self) -> Tuple[X509, str]:
        while True:
            cert_body_path = prompt(
                "Please enter the full path to the certificate body pem file found locally. This is typically called "
                f"cert.pem, and is {fg(1)}NOT{attr(0)} fullchain.pem",
                type=str,
            )
            try:
                with open(cert_body_path, "r") as f:
                    cert_body = f.read()
            except FileNotFoundError:
                logger.warn(
                    f"Could not find cert body with path {cert_body}. Pls try again"
                )
                continue
            if len(cert_body.split("-----END CERTIFICATE-----")) > 2:
                logger.warn(
                    "Certificate body can only have one certificate-- additional ones must go in the chain."
                )
            try:
                cert_obj = load_certificate(FILETYPE_PEM, cert_body)
                return cert_obj, cert_body
            except Error:
                logger.warn("Certificate body is not correct pem cert.")
                continue

    def fetch_cert_chain(self) -> Tuple[Optional[X509], Optional[str]]:
        while True:
            cert_chain_path = prompt(
                "Please enter the full path to the certificate chain/intermediate certificate pem file found locally or "
                "the empty string if there is none. If you used fullchain.pem for the body, or something else saying full "
                "chain then leave this empty.",
                type=str,
                default="",
            )
            if cert_chain_path == "" or cert_chain_path is None:
                return None, None
            try:
                with open(cert_chain_path, "r") as f:
                    cert_chain = f.read()
            except FileNotFoundError:
                logger.warn(
                    f"Could not find cert chain with path {cert_chain}. Pls try again"
                )
                continue
            try:
                cert_chain_obj = load_certificate(FILETYPE_PEM, cert_chain)
                return cert_chain_obj, cert_chain
            except Error:
                logger.warn("certificate chain is not correct pem cert")
                continue

    def get_subject_alternative_names(self, cert_obj: X509) -> List[str]:
        domains_list = []
        for i in range(0, cert_obj.get_extension_count()):
            ext = cert_obj.get_extension(i)
            if "subjectAltName" in str(ext.get_short_name()):
                content = ext.__str__()
                for d in content.split(","):
                    domains_list.append(d.strip()[4:])
        return domains_list
