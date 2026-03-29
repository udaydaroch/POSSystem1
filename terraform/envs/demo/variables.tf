variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "db_password" {
  type      = string
  sensitive = true
}
