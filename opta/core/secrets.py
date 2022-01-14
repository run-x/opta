

# from opta.core.kubernetes import get_manual_secrets


# def configure_kubectl(layer: str) -> None:
#     manual_secrets = get_manual_secrets(self.layer.name)
#     for secret_name in self.module.data.get("secrets", []):
#         if secret_name not in manual_secrets:
#             raise UserErrors(
#                 f"Secret {secret_name} has not been set via opta secret update! Please do so before applying the "
#                 f"K8s service w/ a new secret."
#             )
