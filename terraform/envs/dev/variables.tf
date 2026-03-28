variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key to install on the EC2 instance (e.g. contents of ~/.ssh/id_rsa.pub)"
}
