variable "cluster_name" {
  type = string
}

variable "kubernetes_version" {
  type    = string
  default = "1.29"
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "node_desired" {
  type    = number
  default = 2
}

variable "node_min" {
  type    = number
  default = 1
}

variable "node_max" {
  type    = number
  default = 4
}

variable "node_subnet_ids" {
  type        = list(string)
  description = "Subnets for worker nodes. Defaults to private_subnet_ids when null."
  default     = null
}

variable "create_ecr_repos" {
  type        = bool
  description = "Set to false if ECR repos already exist (e.g. created by the EC2 module)."
  default     = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
