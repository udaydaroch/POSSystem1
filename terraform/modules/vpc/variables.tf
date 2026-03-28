variable "name" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "availability_zones" {
  type = list(string)
}

variable "create_nat_gateway" {
  type        = bool
  default     = false
  description = "Create NAT gateways for private subnets. Costs ~$32/month per AZ. Set false for free tier."
}

variable "tags" {
  type    = map(string)
  default = {}
}
