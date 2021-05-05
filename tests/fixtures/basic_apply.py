BASIC_APPLY = (
    {
        "name": "dev1",
        "org_name": "test",
        "providers": {
            "aws": {"account_id": "abc", "region": "us-east-1", "version": "3.38.0"}
        },
        "modules": [{"name": "core", "type": "aws-base"}],
    },
    {
        "provider": {"aws": {"allowed_account_ids": ["abc"], "region": "us-east-1"}},
        "terraform": {
            "backend": {
                "s3": {
                    "bucket": "opta-tf-state-test-dev1",
                    "key": "dev1",
                    "dynamodb_table": "opta-tf-state-test-dev1",
                    "region": "us-east-1",
                }
            }
        },
        "module": {
            "core": {
                "source": "./config/tf_modules/aws-base",
                "env_name": "dev1",
                "layer_name": "dev1",
                "module_name": "core",
            }
        },
        "output": {
            "kms_account_key_arn": {"value": "${module.core.kms_account_key_arn }"},
            "kms_account_key_id": {"value": "${module.core.kms_account_key_id }"},
            "vpc_id": {"value": "${module.core.vpc_id }"},
            "private_subnet_ids": {"value": "${module.core.private_subnet_ids }"},
            "public_subnets_ids": {"value": "${module.core.public_subnets_ids }"},
        },
    },
)
