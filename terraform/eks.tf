module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "aura-commerce-eks"
  cluster_version = var.eks_cluster_version

  vpc_id     = aws_vpc.aura.id
  subnet_ids = aws_subnet.private[*].id

  eks_managed_node_groups = {
    main = {
      desired_size = 2
      min_size     = 1
      max_size     = 5
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }

  cluster_endpoint_public_access = true
  cluster_endpoint_private_access = true

  tags = {
    Project = "AuraCommerce"
  }
}
