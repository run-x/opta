from modules.base import ModuleProcessor
from opta.exceptions import UserErrors


class AwsVPNProcessor(ModuleProcessor):
    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        vpc_id = self.module.data.get("vpc_id")
        public_subnets_ids = self.module.data.get("public_subnets_ids")
        kms_account_key_arn = self.module.data.get("kms_account_key_arn")
        from_parent = False
        if len(aws_base_modules) == 0 and self.layer.parent is not None:
            from_parent = True
            aws_base_modules = self.layer.parent.get_module_by_type("aws-base")

        if len(aws_base_modules) == 0 and (
            vpc_id is None or public_subnets_ids is None or kms_account_key_arn is None
        ):
            raise UserErrors(
                "You either need to have the base module present or specify a VPC id, security group to give to the"
                "vpn, a kms key to use, and the public subnet ids"
            )

        base_module_source = (
            "data.terraform_remote_state.parent.outputs"
            if from_parent
            else f"module.{aws_base_modules[0].name}"
        )
        self.module.data["vpc_id"] = self.module.data.get(
            "vpc_id", f"${{{{{base_module_source}.vpc_id}}}}"
        )
        self.module.data["public_subnets_ids"] = self.module.data.get(
            "public_subnets_ids", f"${{{{{base_module_source}.public_subnets_ids}}}}"
        )
        self.module.data["kms_account_key_arn"] = self.module.data.get(
            "kms_account_key_arn", f"${{{{{base_module_source}.kms_account_key_arn}}}}"
        )
        super().process(module_idx)
