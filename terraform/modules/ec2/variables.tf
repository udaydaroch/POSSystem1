variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_id" {
  type        = string
  description = "ID of the public subnet to launch the instance in"
}

variable "public_key" {
  type        = string
  description = "SSH public key content (e.g. contents of ~/.ssh/id_rsa.pub)"
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "tags" {
  type    = map(string)
  default = {}
}
