#!/bin/bash
# EC2 User Data script for transaction processor instances
# This script is executed when the EC2 instance starts

set -euo pipefail

# Logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting user-data script at $(date)"

# Export environment variables
export AWS_REGION="${aws_region}"
export ENVIRONMENT="${environment}"
export TRANSACTION_QUEUE_URL="${transaction_queue_url}"
export TRANSACTIONS_TABLE_NAME="${transactions_table_name}"
export IDEMPOTENCY_TABLE_NAME="${idempotency_table_name}"
export S3_BUCKET="${s3_bucket}"

# Get instance metadata
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
export EC2_INSTANCE_ID=$INSTANCE_ID

# Update system packages
echo "Updating system packages..."
dnf update -y

# Install Python 3.12
echo "Installing Python 3.12..."
dnf install -y python3.12 python3.12-pip

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/banking-processor
cd /opt/banking-processor

# Download application from S3
echo "Downloading application..."
aws s3 cp s3://${s3_bucket}/banking-processor/app.zip /opt/banking-processor/app.zip
unzip -o app.zip
rm app.zip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3.12 install -r requirements.txt

# Create environment file
echo "Creating environment file..."
cat > /opt/banking-processor/.env << EOF
AWS_REGION=${aws_region}
ENVIRONMENT=${environment}
TRANSACTION_QUEUE_URL=${transaction_queue_url}
TRANSACTIONS_TABLE_NAME=${transactions_table_name}
IDEMPOTENCY_TABLE_NAME=${idempotency_table_name}
EC2_INSTANCE_ID=$INSTANCE_ID
LOG_LEVEL=INFO
WORKER_THREADS=4
SERVICE_NAME=banking-platform
EOF

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/banking-processor.service << 'SERVICEEOF'
[Unit]
Description=Banking Transaction Processor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/banking-processor
EnvironmentFile=/opt/banking-processor/.env
ExecStart=/usr/bin/python3.12 -m gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    'src.application.app:start_with_worker()'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Enable and start the service
echo "Starting banking processor service..."
systemctl daemon-reload
systemctl enable banking-processor
systemctl start banking-processor

# Wait and verify service is running
sleep 10
if systemctl is-active --quiet banking-processor; then
    echo "Banking processor started successfully"
    # Test health endpoint
    if curl -s http://localhost:8080/health | grep -q "healthy"; then
        echo "Health check passed"
    else
        echo "Health check failed"
    fi
else
    echo "Failed to start banking processor"
    systemctl status banking-processor
    journalctl -u banking-processor --no-pager -n 50
    exit 1
fi

# Install and configure CloudWatch agent
echo "Installing CloudWatch agent..."
dnf install -y amazon-cloudwatch-agent

cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "root"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/user-data.log",
                        "log_group_name": "${log_group_name}",
                        "log_stream_name": "{instance_id}/user-data",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "BankingPlatform/EC2",
        "metrics_collected": {
            "cpu": {
                "measurement": ["cpu_usage_idle", "cpu_usage_user", "cpu_usage_system"],
                "metrics_collection_interval": 60
            },
            "mem": {
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": ["disk_used_percent"],
                "metrics_collection_interval": 60,
                "resources": ["/"]
            }
        },
        "append_dimensions": {
            "InstanceId": "\$${aws:InstanceId}",
            "AutoScalingGroupName": "\$${aws:AutoScalingGroupName}"
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
    -s

echo "User-data script completed at $(date)"
