variable "tenancy_ocid" {
  type = string
}

variable "user_ocid" {
  type = string
}

variable "fingerprint" {
  type = string
}

variable "private_key_path" {
  type = string
}

variable "compartment_id" {
  type = string
}

variable "region" {
  type    = string
  default = "ap-mumbai-1"
}

variable "ssh_public_key" {
  type        = string
  description = "Your local public SSH key to log into the instance"
}