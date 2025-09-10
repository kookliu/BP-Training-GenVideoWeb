# =============================================================================
# Seedance V2 Application Deployment on BytePlus ECS
# =============================================================================

# VPC
resource "byteplus_vpc" "seedance_vpc" {
  vpc_name   = "seedance-v2-vpc"
  cidr_block = "10.0.0.0/16"
}

# Subnet
resource "byteplus_subnet" "seedance_subnet" {
  subnet_name     = "seedance-v2-subnet"
  cidr_block      = "10.0.1.0/24"
  zone_id         = var.availability_zone
  vpc_id          = byteplus_vpc.seedance_vpc.id
}

# Security Group
resource "byteplus_security_group" "seedance_sg" {
  security_group_name = "seedance-v2-sg"
  vpc_id              = byteplus_vpc.seedance_vpc.id
  description         = "Security group for Seedance V2 application"
}

# Security Group Rules
resource "byteplus_security_group_rule" "ssh" {
  security_group_id = byteplus_security_group.seedance_sg.id
  direction         = "ingress"
  protocol          = "tcp"
  port_start        = 22
  port_end          = 22
  cidr_ip           = "0.0.0.0/0"
  description       = "Allow SSH"
}

resource "byteplus_security_group_rule" "http" {
  security_group_id = byteplus_security_group.seedance_sg.id
  direction         = "ingress"
  protocol          = "tcp"
  port_start        = 80
  port_end          = 80
  cidr_ip           = "0.0.0.0/0"
  description       = "Allow HTTP"
}

resource "byteplus_security_group_rule" "https" {
  security_group_id = byteplus_security_group.seedance_sg.id
  direction         = "ingress"
  protocol          = "tcp"
  port_start        = 443
  port_end          = 443
  cidr_ip           = "0.0.0.0/0"
  description       = "Allow HTTPS"
}

resource "byteplus_security_group_rule" "gradio" {
  security_group_id = byteplus_security_group.seedance_sg.id
  direction         = "ingress"
  protocol          = "tcp"
  port_start        = 7860
  port_end          = 7860
  cidr_ip           = "0.0.0.0/0"
  description       = "Allow Gradio Web UI"
}

resource "byteplus_security_group_rule" "egress" {
  security_group_id = byteplus_security_group.seedance_sg.id
  direction         = "egress"
  protocol          = "all"
  port_start        = -1
  port_end          = -1
  cidr_ip           = "0.0.0.0/0"
  description       = "Allow all outbound traffic"
}

# EIP (Elastic IP)
resource "byteplus_eip_address" "seedance_eip" {
  billing_type = "PostPaidByTraffic"
  bandwidth    = 20  # Higher bandwidth for video generation
  isp          = "BGP"
  name         = "seedance-v2-eip"
  description  = "EIP for Seedance V2 application"
}

# SSH Key Pair
resource "byteplus_ecs_key_pair" "seedance_key" {
  key_pair_name = var.key_pair_name
  key_file      = "${var.key_pair_name}.pem"
  description   = "SSH key pair for Seedance V2 deployment"
}

# Data source for Ubuntu 24.04 image
data "byteplus_images" "ubuntu24" {
  os_type    = "Linux"
  visibility = "public"
  name_regex = "Ubuntu 24.04 64 bit"
}

# ECS Instance
resource "byteplus_ecs_instance" "seedance_instance" {
  instance_name        = var.instance_name
  instance_type        = var.instance_type
  image_id            = [for image in data.byteplus_images.ubuntu24.images : image.image_id if image.image_name == "Ubuntu 24.04 64 bit"][0]
  subnet_id           = byteplus_subnet.seedance_subnet.id
  security_group_ids  = [byteplus_security_group.seedance_sg.id]
  instance_charge_type = "PostPaid"
  system_volume_type   = "ESSD_PL0"
  system_volume_size   = 50  # Larger disk for application and logs
  
  # Key pair for SSH access
  key_pair_name = byteplus_ecs_key_pair.seedance_key.key_pair_name
  
  # Minimal user data script for basic system setup only
  user_data = base64encode(file("${path.module}/user-data.sh"))
  
  # Tags
  tags {
    key   = "Environment"
    value = "Production"
  }
  
  tags {
    key   = "Application"
    value = "Seedance-V2"
  }
  
  tags {
    key   = "Project"
    value = "BytePlus-GenVideo"
  }

}

# EIP Association
resource "byteplus_eip_associate" "seedance_eip_assoc" {
  allocation_id = byteplus_eip_address.seedance_eip.id
  instance_id   = byteplus_ecs_instance.seedance_instance.id
  instance_type = "EcsInstance"
}