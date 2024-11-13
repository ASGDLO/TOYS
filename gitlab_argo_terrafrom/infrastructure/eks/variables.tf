variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "public_subnets" {
  description = "List of public subnet IDs"
  type        = list(string)
}