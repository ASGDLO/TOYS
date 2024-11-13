provider "aws" {
  region = var.region
}

provider "kubernetes" {
  host                   = aws_eks_cluster.demo.endpoint
  token                  = data.aws_eks_cluster_auth.demo.token
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.demo.certificate_authority[0].data)
}

resource "aws_iam_role" "eks_cluster" {
  name = "eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  ]
}

resource "aws_eks_cluster" "demo" {
  name     = "demo-cluster"
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids = var.public_subnets
  }

  depends_on = [
    aws_iam_role.eks_cluster
  ]
}

data "aws_eks_cluster_auth" "demo" {
  name = aws_eks_cluster.demo.name
}

output "eks_cluster_name" {
  value = aws_eks_cluster.demo.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.demo.endpoint
}

output "eks_cluster_certificate_authority" {
  value = aws_eks_cluster.demo.certificate_authority[0].data
}