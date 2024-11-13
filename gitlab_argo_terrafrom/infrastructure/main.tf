module "vpc" {
  source = "./vpc"

  region = var.region
}

module "eks" {
  source = "./eks"

  region        = var.region
  public_subnets = module.vpc.public_subnets
}