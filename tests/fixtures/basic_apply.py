BASIC_APPLY = (
    {
        "name": "dev1",
        "org_name": "test",
        "providers": {"aws": {"account_id": "111111111111", "region": "us-east-1"}},
        "modules": [{"name": "core", "type": "aws-base"}],
    },
    {
        "provider": {
            "aws": {"allowed_account_ids": ["111111111111"], "region": "us-east-1"}
        },
        "terraform": {
            "backend": {
                "s3": {
                    "bucket": "opta-tf-state-test-dev1-98f2",
                    "key": "dev1",
                    "dynamodb_table": "opta-tf-state-test-dev1-98f2",
                    "region": "us-east-1",
                }
            },
            "required_providers": {
                "aws": {"source": "hashicorp/aws", "version": "4.21.0"},
                "helm": {"source": "hashicorp/helm", "version": "2.6.0"},
            },
        },
        "module": {
            "core": {
                "source": "./modules/aws_base/tf_module",
                "env_name": "dev1",
                "layer_name": "dev1",
                "module_name": "core",
                "private_ipv4_cidr_blocks": [
                    "10.0.128.0/21",
                    "10.0.136.0/21",
                    "10.0.144.0/21",
                ],
                "public_ipv4_cidr_blocks": ["10.0.0.0/21", "10.0.8.0/21", "10.0.16.0/21"],
                "total_ipv4_cidr_block": "10.0.0.0/16",
                "vpc_log_retention": 90,
                "vpc_id": None,
                "public_subnet_ids": None,
                "private_subnet_ids": None,
            }
        },
        "output": {
            "kms_account_key_arn": {"value": "${module.core.kms_account_key_arn }"},
            "kms_account_key_id": {"value": "${module.core.kms_account_key_id }"},
            "vpc_id": {"value": "${module.core.vpc_id }"},
            "private_subnet_ids": {"value": "${module.core.private_subnet_ids }"},
            "public_subnets_ids": {"value": "${module.core.public_subnets_ids }"},
            "s3_log_bucket_name": {"value": "${module.core.s3_log_bucket_name }"},
            "public_nat_ips": {"value": "${module.core.public_nat_ips }"},
            "state_storage": {"value": "opta-tf-state-test-dev1-98f2"},
            "providers": {
                "value": {"aws": {"account_id": "111111111111", "region": "us-east-1"}}
            },
        },
    },
)
