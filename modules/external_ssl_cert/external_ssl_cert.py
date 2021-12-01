import os
from typing import TYPE_CHECKING, List, Tuple

from OpenSSL.crypto import (
    FILETYPE_PEM,
    X509,
    Error,
    PKey,
    dump_publickey,
    load_certificate,
    load_privatekey,
)

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class ExternalSSLCert(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(ExternalSSLCert, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        private_key_obj, private_key_str = self.fetch_private_key()
        cert_body_obj, cert_body_str = self.fetch_cert_body()
        cert_pub = dump_publickey(FILETYPE_PEM, cert_body_obj.get_pubkey())
        key_pub = dump_publickey(FILETYPE_PEM, private_key_obj)
        if cert_pub != key_pub:
            raise UserErrors(
                "Certificate private key does not match inputted private key, try again"
            )
        cert_chain_obj, cert_chain_str = self.fetch_cert_chain()
        self.module.data["private_key"] = private_key_str
        self.module.data["certificate_body"] = cert_body_str
        self.module.data["certificate_chain"] = cert_chain_str
        # TODO: add cert chain validation and full chain validation against trusted CA
        domains_list = self.get_subject_alternative_names(cert_body_obj)
        if self.module.data["domain"] not in domains_list:
            raise UserErrors(
                f"You provided a domain of {self.module.data['domain']} but the cert is only for domains {domains_list}"
            )
        super(ExternalSSLCert, self).process(module_idx)

    def fetch_private_key(self) -> Tuple[PKey, str]:
        private_key_file: str = os.path.join(
            os.path.dirname(self.layer.path), self.module.data["private_key_file"]
        )
        try:
            with open(private_key_file, "r") as f:
                privkey = f.read()
        except FileNotFoundError:
            raise UserErrors(
                f"Could not find private key with path {private_key_file}. Pls try again"
            )
        try:
            private_key_obj = load_privatekey(FILETYPE_PEM, privkey)
            return private_key_obj, privkey
        except Error:
            raise UserErrors("private key is not correct pem private key")

    def fetch_cert_body(self) -> Tuple[X509, str]:
        certificate_body_file: str = os.path.join(
            os.path.dirname(self.layer.path), self.module.data["certificate_body_file"]
        )
        try:
            with open(certificate_body_file, "r") as f:
                cert_body = f.read()
        except FileNotFoundError:
            raise UserErrors(
                f"Could not find cert body with path {certificate_body_file}. Pls try again"
            )
        if len(cert_body.split("-----END CERTIFICATE-----")) > 2:
            raise UserErrors(
                "Certificate body can only have one certificate-- additional ones must go in the chain."
            )
        try:
            cert_obj = load_certificate(FILETYPE_PEM, cert_body.encode("utf-8"))
            return cert_obj, cert_body
        except Error:
            raise UserErrors("Certificate body is not correct pem cert.")

    def fetch_cert_chain(self) -> Tuple[X509, str]:
        certificate_chain_file: str = os.path.join(
            os.path.dirname(self.layer.path), self.module.data["certificate_chain_file"]
        )
        try:
            with open(certificate_chain_file, "r") as f:
                cert_chain = f.read()
        except FileNotFoundError:
            raise UserErrors(
                f"Could not find cert chain with path {certificate_chain_file}. Pls try again"
            )
        try:
            cert_chain_obj = load_certificate(FILETYPE_PEM, cert_chain.encode("utf-8"))
            return cert_chain_obj, cert_chain
        except Error:
            raise UserErrors("certificate chain is not correct pem cert")

    def get_subject_alternative_names(self, cert_obj: X509) -> List[str]:
        domains_list = []
        for i in range(0, cert_obj.get_extension_count()):
            ext = cert_obj.get_extension(i)
            if "subjectAltName" in str(ext.get_short_name()):
                content = ext.__str__()
                for d in content.split(","):
                    domains_list.append(d.strip()[4:])
        return domains_list
