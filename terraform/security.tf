resource "aws_security_group" "eks" {
  name        = "aura-eks-sg"
  description = "EKS cluster node security group"
  vpc_id      = aws_vpc.aura.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    from_port   = 10250
    to_port     = 10250
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
    Name = "aura-eks-sg"
  }
}

resource "aws_security_group" "lambda" {
  name        = "aura-lambda-sg"
  description = "Lambda function security group"
  vpc_id      = aws_vpc.aura.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aura-lambda-sg"
  }
}
