resource "aws_security_group" "db" {
  name        = "opta-${var.layer_name}-db-sg"
  description = "For usage by databases to give access to resources in the vpc"
  vpc_id      = local.vpc_id

  ingress {
    description = "postgres"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = local.vpc_cidr_blocks
  }

  ingress {
    description = "mysql"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = local.vpc_cidr_blocks
  }
}

resource "aws_security_group" "elasticache" {
  name        = "opta-${var.layer_name}-elasticache-sg"
  description = "For usage by elasticache to give access to resources in the vpc"
  vpc_id      = local.vpc_id

  # https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/elasticache-vpc-accessing.html
  ingress {
    description = "redis"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = local.vpc_cidr_blocks
  }

}

resource "aws_security_group" "documentdb" {
  name        = "opta-${var.layer_name}-documentdb-sg"
  description = "For usage by documentdb to give access to resources in the vpc"
  vpc_id      = local.vpc_id

  # https://docs.aws.amazon.com/documentdb/latest/developerguide/db-cluster-create.html
  ingress {
    description = "documentdb"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = local.vpc_cidr_blocks
  }
}


resource "aws_security_group" "vpn" {
  name_prefix = "opta-${var.env_name}-vpn"
  description = "VPN security group."
  vpc_id      = local.vpc_id

  tags = {
    "Name" = "opta-${var.env_name}-vpn"
  }

  ingress {
    description = "allowssh"
    from_port   = 443
    protocol    = "tcp"
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "alloutbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    # To be fixed - for now user can create an SG manually to override.
    #tfsec:ignore:aws-vpc-no-public-egress-sgr
    cidr_blocks = ["0.0.0.0/0"]
  }
}
