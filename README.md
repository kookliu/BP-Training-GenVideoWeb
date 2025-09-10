# BP-Training-GenVideoWeb

## 🚀 Seedance V2 Video Generation Platform

A comprehensive AI video generation platform powered by BytePlus Seedance models, featuring automated Terraform deployment on BytePlus Cloud Infrastructure.

### ✨ Features

- **🎥 Advanced Video Generation**: Support for Text-to-Video and Image-to-Video generation
- **🧠 Multiple AI Models**: 
  - Seedance 1.0 Pro (High-quality generation)
  - Seedance 1.0 Lite T2V (Fast text-to-video)
  - Seedance 1.0 Lite I2V (Fast image-to-video)
- **🌐 Web Interface**: User-friendly Gradio web interface
- **☁️ Cloud Deployment**: Automated infrastructure provisioning with Terraform
- **🔒 Secure Configuration**: Environment-based API key management
- **📊 Real-time Monitoring**: Built-in logging and status tracking

---

## 📁 Project Structure

```
BP-Training-GenVideoWeb/
├── README.md                           # This file - main project documentation
└── terraform-seedance-v2/             # Terraform deployment configuration
    ├── main.tf                         # Main Terraform configuration
    ├── variables.tf                    # Variable definitions
    ├── outputs.tf                      # Output definitions
    ├── providers.tf                    # Provider configuration
    ├── user-data.sh                    # EC2 user data script
    ├── terraform.tfvars.example        # Example configuration file
    ├── .gitignore                      # Git ignore rules
    ├── MANUAL_DEPLOYMENT.md            # Manual deployment guide
    ├── TROUBLESHOOTING.md              # Troubleshooting guide
    └── seedance-v2/                    # Application source code
        ├── app.py                      # Main Gradio application
        ├── requirements.txt            # Python dependencies
        └── README.md                   # Application documentation
```

---

## 🛠️ Deployment Options

### Option 1: Automated Terraform Deployment (Recommended)

#### Prerequisites
- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- BytePlus Cloud account with API access
- BytePlus API credentials (Access Key & Secret Key)
- BytePlus Seedance API key

#### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/kookliu/BP-Training-GenVideoWeb.git
   cd BP-Training-GenVideoWeb/terraform-seedance-v2
   ```

2. **Configure credentials**
   ```bash
   # Copy example configuration
   cp terraform.tfvars.example terraform.tfvars
   
   # Edit configuration with your credentials
   vi terraform.tfvars
   ```

3. **Initialize and deploy**
   ```bash
   # Initialize Terraform
   terraform init
   
   # Plan deployment
   terraform plan
   
   # Deploy infrastructure
   terraform apply
   ```

4. **Access your application**
   ```bash
   # Get public IP from outputs
   terraform output public_ip
   
   # Access web interface
   # http://YOUR_PUBLIC_IP
   ```

#### Configuration Variables

Create `terraform.tfvars` file with your credentials:

```hcl
# BytePlus Cloud Credentials
access_key = "your_byteplus_access_key"
secret_key = "your_byteplus_secret_key"

# BytePlus Seedance API
byteplus_api_key = "your_seedance_api_key"
byteplus_base_url = "https://open.byteplusapi.com"

# Optional: Customize deployment
region = "ap-southeast-1"
instance_type = "ecs.g3i.large"
instance_name = "my-seedance-server"
```

### Option 2: Manual Deployment

If you prefer manual deployment or need custom configuration, follow the detailed manual deployment guide:

📖 **[Manual Deployment Guide](terraform-seedance-v2/MANUAL_DEPLOYMENT.md)**

---

## 🏗️ Infrastructure Components

The Terraform configuration creates the following resources:

### Compute Resources
- **ECS Instance**: GPU-enabled instance for AI workloads (`ecs.g3i.large`)
- **Key Pair**: SSH key pair for secure access
- **Security Group**: Firewall rules for HTTP/HTTPS/SSH access

### Network Resources
- **VPC**: Virtual Private Cloud with custom CIDR
- **Subnet**: Public subnet for internet access
- **Internet Gateway**: For external connectivity
- **Route Table**: Routing configuration

### Application Stack
- **Ubuntu 22.04**: Latest LTS operating system
- **Python 3.12**: Latest Python runtime
- **Nginx**: Reverse proxy and web server
- **Systemd**: Service management
- **Virtual Environment**: Isolated Python dependencies

---

## 🎮 Using the Application

### Web Interface Features

1. **Model Selection**
   - Choose between Pro and Lite models
   - Select Text-to-Video or Image-to-Video generation

2. **Input Configuration**
   - **Text Prompt**: Describe your desired video content
   - **Image Upload**: Upload reference image (I2V mode)
   - **Advanced Settings**: Configure duration, resolution, and quality

3. **Generation Process**
   - Real-time progress tracking
   - Status updates and error handling
   - Automatic retry mechanisms

4. **Output Management**
   - Video preview and download
   - Generation history
   - Export options

### API Models Available

| Model | Type | Use Case | Speed | Quality |
|-------|------|----------|--------|---------|
| Seedance 1.0 Pro | T2V | High-quality text-to-video | Slower | Highest |
| Seedance 1.0 Lite T2V | T2V | Fast text-to-video | Fast | Good |
| Seedance 1.0 Lite I2V | I2V | Fast image-to-video | Fast | Good |

---

## 🔧 Management & Operations

### Service Management
```bash
# SSH into server
ssh -i seedance-keypair.pem root@YOUR_PUBLIC_IP

# Service operations
systemctl status seedance    # Check status
systemctl restart seedance   # Restart service
systemctl stop seedance      # Stop service
systemctl start seedance     # Start service

# View logs
journalctl -u seedance -f    # Follow logs
```

### Application Updates
```bash
# Navigate to application directory
cd /opt/seedance-v2

# Update application code
curl -L -o app.py "https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/terraform-seedance-v2/seedance-v2/app.py"

# Restart service
systemctl restart seedance
```

### Infrastructure Updates
```bash
# Navigate to terraform directory
cd terraform-seedance-v2

# Apply configuration changes
terraform plan
terraform apply
```

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. Application Won't Start
```bash
# Check service logs
journalctl -u seedance -n 50

# Verify API credentials
systemctl show seedance --property=Environment

# Test manual startup
cd /opt/seedance-v2
source venv/bin/activate
python3 app.py
```

#### 2. Cannot Access Web Interface
```bash
# Check port listening
netstat -tlnp | grep -E "(80|7860)"

# Verify nginx status
systemctl status nginx

# Check security group settings in BytePlus console
```

#### 3. Video Generation Fails
- Verify BytePlus API key is correct
- Check API quota and limits
- Review application logs for specific errors

📖 **[Complete Troubleshooting Guide](terraform-seedance-v2/TROUBLESHOOTING.md)**

---

## 📊 Monitoring & Logs

### Application Logs
```bash
# Real-time application logs
journalctl -u seedance -f

# Error logs from last hour
journalctl -u seedance --since "1 hour ago" -p err

# Nginx access logs
tail -f /var/log/nginx/access.log
```

### System Monitoring
```bash
# System resource usage
htop

# Disk usage
df -h

# Network connections
netstat -tuln
```

---

## 🔒 Security Considerations

### API Key Security
- API keys are stored as environment variables
- Service files have restricted permissions (600)
- Keys are not logged or exposed in web interface

### Network Security
- Security groups restrict access to necessary ports only
- SSH access requires private key authentication
- HTTPS can be configured with Let's Encrypt (manual setup)

### System Security
- Regular system updates recommended
- Firewall rules configured via security groups
- Root access via SSH key only

---

## 🏃‍♂️ Quick Commands Reference

### Deployment
```bash
# Quick deploy
git clone https://github.com/kookliu/BP-Training-GenVideoWeb.git
cd BP-Training-GenVideoWeb/terraform-seedance-v2
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your credentials
terraform init && terraform apply
```

### Management
```bash
# SSH connect
ssh -i seedance-keypair.pem root@$(terraform output -raw public_ip)

# Service control
systemctl {start|stop|restart|status} seedance

# View logs
journalctl -u seedance -f

# Update app
cd /opt/seedance-v2 && curl -L -o app.py "https://raw.githubusercontent.com/kookliu/BP-Training-GenVideoWeb/main/terraform-seedance-v2/seedance-v2/app.py" && systemctl restart seedance
```

### Cleanup
```bash
# Destroy infrastructure
terraform destroy
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test deployment
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/kookliu/BP-Training-GenVideoWeb/issues)
- **Documentation**: Check the `terraform-seedance-v2/` directory for detailed guides
- **BytePlus Support**: [BytePlus Documentation](https://byteplusapi.com/docs)

---

## 🎯 What's Next?

- [ ] HTTPS/SSL certificate automation
- [ ] Multi-region deployment support
- [ ] Auto-scaling configuration
- [ ] Monitoring dashboard integration
- [ ] CI/CD pipeline setup

---

**Ready to generate amazing AI videos? Start with the Quick Start guide above!** 🚀
