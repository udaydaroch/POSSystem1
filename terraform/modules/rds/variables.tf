variable "identifier" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "app_security_group_id" {
  type        = string
  description = "Security group ID of the application (EC2) that is allowed to connect to RDS"
}

variable "db_username" {
  type    = string
  default = "prism"
}

variable "db_password" {
  type      = string
  sensitive = true

  validation {
    condition     = !can(regex("[/@\" ]", var.db_password))
    error_message = "db_password must not contain '/', '@', '\"', or spaces (RDS restriction)."
  }
}

variable "instance_class" {
  type        = string
  default     = "db.t3.micro"
  description = "db.t3.micro is free-tier eligible (750 hrs/month)"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "multi_az" {
  type    = bool
  default = false
}

variable "deletion_protection" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
