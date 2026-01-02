#!/bin/bash
# EC2 User Data script for transaction processor instances
# This script is executed when the EC2 instance starts

set -euo pipefail

# Logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting user-data script at $(date)"

# Update system packages
echo "Updating system packages..."
yum update -y

# Install Python 3.12
echo "Installing Python 3.12..."
yum install -y python3.12 python3.12-pip

# Install application dependencies
echo "Installing application dependencies..."
pip3.12 install boto3 botocore pydantic pydantic-settings flask gunicorn aws-lambda-powertools orjson

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/banking-processor
cd /opt/banking-processor

# Download application from S3 (assumes code is deployed to S3)
echo "Downloading application..."
aws s3 cp s3://${S3_BUCKET}/banking-processor/app.zip /opt/banking-processor/app.zip
unzip -o app.zip

# Set environment variables
echo "Setting environment variables..."
cat > /opt/banking-processor/.env << EOF
AWS_REGION=${AWS_REGION}
TRANSACTION_QUEUE_URL=${TRANSACTION_QUEUE_URL}
TRANSACTIONS_TABLE_NAME=${TRANSACTIONS_TABLE_NAME}
IDEMPOTENCY_TABLE_NAME=${IDEMPOTENCY_TABLE_NAME}
ENVIRONMENT=${ENVIRONMENT}
LOG_LEVEL=INFO
WORKER_THREADS=4
EOF

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/banking-processor.service << EOF
[Unit]
Description=Banking Transaction Processor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/banking-processor
EnvironmentFile=/opt/banking-processor/.env
ExecStart=/usr/bin/python3.12 -m gunicorn \
    --config src/application/gunicorn_config.py \
    src.application.app:create_app()
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "Starting banking processor service..."
systemctl daemon-reload
systemctl enable banking-processor
systemctl start banking-processor

# Verify service is running
sleep 5
if systemctl is-active --quiet banking-processor; then
    echo "Banking processor started successfully"
else
    echo "Failed to start banking processor"
    systemctl status banking-processor
    exit 1
fi

# Install CloudWatch agent for monitoring
echo "Installing CloudWatch agent..."
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
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
                        "file_path": "/var/log/banking-processor.log",
                        "log_group_name": "/banking/processor",
                        "log_stream_name": "{instance_id}",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    },
    "metrics": {
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
                "metrics_collection_interval": 60
            }
        },
        "append_dimensions": {
            "InstanceId": "\${aws:InstanceId}",
            "AutoScalingGroupName": "\${aws:AutoScalingGroupName}"
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
