output "instance_id" {
  description = "ID of the ECS instance"
  value       = byteplus_ecs_instance.seedance_instance.id
}

output "public_ip" {
  description = "Public IP address of the instance"
  value       = byteplus_eip_address.seedance_eip.eip_address
}

output "server_ip" {
  description = "Server IP address for manual deployment"
  value       = byteplus_eip_address.seedance_eip.eip_address
}

output "application_url" {
  description = "URL to access the Seedance V2 application"
  value       = "http://${byteplus_eip_address.seedance_eip.eip_address}"
}

output "gradio_direct_url" {
  description = "Direct URL to access Gradio interface"
  value       = "http://${byteplus_eip_address.seedance_eip.eip_address}:7860"
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${var.key_pair_name}.pem root@${byteplus_eip_address.seedance_eip.eip_address}"
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = byteplus_vpc.seedance_vpc.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = byteplus_subnet.seedance_subnet.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = byteplus_security_group.seedance_sg.id
}
