variable "access_key" {
  description = "BytePlus Access Key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "BytePlus Secret Key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "BytePlus Region"
  type        = string
  default     = "ap-southeast-1"
}

variable "availability_zone" {
  description = "Availability Zone for ECS instance"
  type        = string
  default     = "ap-southeast-1a"
}

variable "instance_name" {
  description = "Name of the ECS instance"
  type        = string
  default     = "seedance-v2-server"
}

variable "instance_type" {
  description = "ECS instance type"
  type        = string
  default     = "ecs.g3i.large"  # GPU instance for AI workload
}

variable "key_pair_name" {
  description = "Name of the SSH key pair"
  type        = string
  default     = "seedance-keypair"
}

variable "byteplus_api_key" {
  description = "BytePlus API Key for Seedance application"
  type        = string
  sensitive   = true
}

variable "byteplus_base_url" {
  description = "BytePlus Base URL for Seedance application"
  type        = string
  default     = "https://open.byteplusapi.com"
}