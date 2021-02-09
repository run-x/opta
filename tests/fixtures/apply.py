BASIC_APPLY = (
                {
                    "meta": {
                        "create-env": "dev1",
                        "name": "dev1",
                        "providers": {
                            "aws": {"allowed_account_ids": ["abc"], "region": "us-east-1"}
                        },
                    },
                    "modules": [
                        {
                            "core": {
                                "type": "aws-state-init",
                                "bucket_name": "{state_storage}",
                                "dynamodb_lock_table_name": "{state_storage}",
                            }
                        }
                    ],
                },
                {
                    "provider": {
                        "aws": {"allowed_account_ids": ["abc"], "region": "us-east-1"}
                    },
                    "terraform": {
                        "backend": {
                            "s3": {
                                "bucket": "opta-tf-state-dev1",
                                "key": "dev1",
                                "dynamodb_table": "opta-tf-state-dev1",
                                "region": "us-east-1",
                            }
                        }
                    },
                    "module": {
                        "core": {
                            "source": "./config/tf_modules/aws-state-init",
                            "bucket_name": "opta-tf-state-dev1",
                            "dynamodb_lock_table_name": "opta-tf-state-dev1",
                        }
                    },
                    "output": {
                        "state_bucket_id": {"value": "${module.core.state_bucket_id }"},
                        "state_bucket_arn": {"value": "${module.core.state_bucket_arn }"},
                        "kms_account_key_arn": {
                            "value": "${module.core.kms_account_key_arn }"
                        },
                        "kms_account_key_id": {
                            "value": "${module.core.kms_account_key_id }"
                        },
                    },
                },
            )