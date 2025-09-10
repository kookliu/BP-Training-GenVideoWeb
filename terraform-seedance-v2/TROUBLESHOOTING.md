# 🔧 Seedance V2 - 故障排除指南

## 常见部署问题及解决方案

### 1. 目录不存在错误
**错误**: `cd: /opt/seedance-v2: No such file or directory`

**原因**: 应用目录未在初始化时创建完成

**解决方案**:
```bash
# 方法1: 重新运行完整部署
./deploy-app.sh --destroy
./deploy-app.sh

# 方法2: 手动检查服务器状态
ssh -i seedance-keypair.pem root@<SERVER_IP>
sudo mkdir -p /opt/seedance-v2
```

### 2. Python 虚拟环境错误
**错误**: `Failed to activate virtual environment!` 或 `venv/bin/activate: No such file or directory`

**原因**: Python 虚拟环境未正确创建或已损坏

**诊断步骤**:
```bash
# 1. 使用调试脚本检查环境
./debug-venv.sh

# 2. SSH 到服务器检查
ssh -i seedance-keypair.pem root@<SERVER_IP>
cd /opt/seedance-v2
ls -la venv/bin/
```

**解决方案**:
```bash
# 方法1: 重新创建虚拟环境
ssh -i seedance-keypair.pem root@<SERVER_IP>
cd /opt/seedance-v2
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 方法2: 如果 python3 不可用，安装完整的 Python
apt-get update
apt-get install -y python3-full python3-venv python3-pip
python3 -m venv venv

# 方法3: 重新运行应用更新
./deploy-app.sh --update-only
```

### 3. systemd 服务未找到
**错误**: `Unit seedance.service could not be found`

**原因**: systemd 服务文件未创建

**解决方案**:
```bash
# 运行应用更新会自动创建服务
./deploy-app.sh --update-only

# 或手动创建服务
ssh -i seedance-keypair.pem root@<SERVER_IP>
# 然后手动创建 /etc/systemd/system/seedance.service
```

### 4. SSH 连接失败
**错误**: `Permission denied` 或 `Connection timeout`

**解决方案**:
```bash
# 检查密钥文件权限
chmod 600 seedance-keypair.pem

# 检查服务器状态
./deploy-app.sh --status

# 重新生成密钥
rm -f seedance-keypair.pem
./deploy-app.sh
```

### 5. 应用启动失败
**错误**: 服务状态显示 `failed` 或 `inactive`

**解决方案**:
```bash
# 检查应用日志
ssh -i seedance-keypair.pem root@<SERVER_IP>
sudo journalctl -u seedance -f

# 检查应用文件
ls -la /opt/seedance-v2/
cat /opt/seedance-v2/app.py

# 手动测试应用
cd /opt/seedance-v2
source venv/bin/activate
python app.py
```

### 6. API 密钥配置问题
**错误**: `ARK_API_KEY environment variable is not set`

**解决方案**:
```bash
# 检查 terraform.tfvars 配置
cat terraform.tfvars | grep byteplus_api_key

# 检查服务环境变量
ssh -i seedance-keypair.pem root@<SERVER_IP>
sudo systemctl show seedance --property=Environment
```

### 7. 网络连接问题
**错误**: 无法访问应用或下载失败

**解决方案**:
```bash
# 检查安全组规则
./deploy-app.sh --status

# 检查服务器网络
ssh -i seedance-keypair.pem root@<SERVER_IP>
curl -I http://localhost:7860
ping -c 3 google.com

# 检查 Nginx 状态
sudo systemctl status nginx
```

## 🔍 诊断命令

### 快速状态检查
```bash
./deploy-app.sh --status
```

### 详细日志查看
```bash
ssh -i seedance-keypair.pem root@<SERVER_IP> << 'EOF'
echo "=== System Info ==="
df -h
free -h
echo "=== Seedance Service ==="
sudo systemctl status seedance
echo "=== Recent Logs ==="
sudo journalctl -u seedance --lines=20
echo "=== Nginx Status ==="
sudo systemctl status nginx
EOF
```

### 环境验证
```bash
ssh -i seedance-keypair.pem root@<SERVER_IP> << 'EOF'
echo "=== Directory Structure ==="
ls -la /opt/seedance-v2/
echo "=== Python Environment ==="
/opt/seedance-v2/venv/bin/python --version
echo "=== Environment Variables ==="
sudo systemctl show seedance --property=Environment
EOF
```

## 🚨 紧急恢复

### 完全重新部署
```bash
# 销毁所有资源
./deploy-app.sh --destroy

# 等待 1-2 分钟后重新部署
./deploy-app.sh
```

### 仅重置应用
```bash
# 备份配置
cp terraform.tfvars terraform.tfvars.backup

# 重新部署应用
./deploy-app.sh --update-only
```

## 📞 获取帮助

1. **检查日志**: 始终先查看服务日志
2. **运行测试**: 使用 `./test-deployment.sh` 验证配置
3. **状态检查**: 使用 `./deploy-app.sh --status` 查看当前状态
4. **文档参考**: 查看 README.md 和 QUICK_START.md

### 收集诊断信息
运行以下命令收集完整的诊断信息：

```bash
# 创建诊断报告
./deploy-app.sh --status > diagnostic-report.txt 2>&1
echo "--- Server Details ---" >> diagnostic-report.txt
ssh -i seedance-keypair.pem root@<SERVER_IP> 'sudo journalctl -u seedance --lines=50' >> diagnostic-report.txt 2>&1
```

将 `diagnostic-report.txt` 发送给技术支持以获得帮助。