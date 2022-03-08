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
} {
  waiver := {
    "rule_id": "FG_R00010",
    "resource_id": "aws_cloudfront_distribution.distribution"
  }
} {
  waiver := {
    "rule_id": "FG_R00067",
    "resource_id": "aws_cloudfront_distribution.distribution"
  }
} {
  waiver := {
    "rule_id": "FG_R00274",
    "resource_id": "aws_s3_bucket.bucket"
  }
} {
  waiver := {
    "rule_id": "FG_R00068",
    "resource_id": "aws_cloudwatch_log_group.logs"
  }
} {
  waiver := {
    "rule_id": "FG_R00229",
    "resource_id": "aws_s3_bucket.log_bucket"
  }
} {
  waiver := {
    "rule_id": "FG_R00099",
    "resource_id": "aws_s3_bucket.log_bucket"
  }
}  {
  waiver := {
    "rule_id": "FG_R00101",
    "resource_id": "aws_s3_bucket.log_bucket"
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
} {
  rule := {
    "rule_id": "FG_R00227",
    "status": "DISABLED"
  }
} {
  rule := {
    "rule_id": "FG_R00433",
    "status": "DISABLED"
  }
} {
  rule := {
    "rule_id": "FG_R00018",
    "status": "DISABLED"
  }
} {
  rule := {
    "rule_id": "FG_R00073",
    "status": "DISABLED"
  }
}