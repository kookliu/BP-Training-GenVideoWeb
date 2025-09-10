terraform {
  required_version = ">= 1.0" 
  required_providers {
    byteplus = {
      source  = "byteplus-sdk/byteplus"
      version = "~> 0.0.1"
    }
  }
}

# Configure the BytePlus Provider
provider "byteplus" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = var.region
  endpoint   = "open.ap-southeast-1.byteplusapi.com"
}
