resource "aws_db_subnet_group" "aura" {
  name       = "aura-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "aura-db-subnet"
  }
}

resource "aws_security_group" "rds" {
  name        = "aura-rds-sg"
  description = "Security group for AuraCommerce PostgreSQL RDS"
  vpc_id      = aws_vpc.aura.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aura-rds-sg"
  }
}

resource "aws_db_instance" "aura" {
  identifier             = "aura-commerce-db"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = "db.t3.medium"
  allocated_storage      = 50
  max_allocated_storage  = 500
  storage_type           = "gp3"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.aura.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  publicly_accessible    = false
  multi_az               = var.environment == "production"

  tags = {
    Name = "aura-commerce-rds"
  }
}
