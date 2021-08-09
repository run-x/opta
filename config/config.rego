package fugue.regula.config

waivers[waiver] {
  waiver := {
    "rule_id": "FG_R00068",
    "resource_id": "aws_cloudwatch_log_group.cluster_logs"
  }
} {
  waiver := {
    "rule_id": "FG_R00209",
    "resource_id": "aws_rds_cluster.db_cluster"
  }
} {
  waiver := {
    "rule_id": "FG_R00274",
    "resource_id": "aws_s3_bucket.log_bucket"
  }
} {
  waiver := {
    "rule_id": "FG_R00100",
    "resource_id": "aws_s3_bucket.bucket"
  }
}

rules[rule] {
  rule := {
    "rule_id": "FG_R00272",
    "status": "DISABLED"
  }
} {
  rule := {
    "rule_id": "FG_R00007",
    "status": "DISABLED"
  }
} {
  rule := {
    "rule_id": "FG_R00275",
    "status": "DISABLED"
  }
}