variable "aws_region" {
  type    = string
  default = "ap-southeast-2"  # Sydney — closest to NZ
}

variable "db_password" {
  type      = string
  sensitive = true
  # Set via: export TF_VAR_db_password="your-secure-password"
  # Or in a terraform.tfvars file (never commit that file)
}
