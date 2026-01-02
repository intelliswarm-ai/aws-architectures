#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_DIR/terraform"

# Default values
ENVIRONMENT="dev"
ACTION="apply"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --destroy)
            ACTION="destroy"
            shift
            ;;
        --plan)
            ACTION="plan"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Deploying aws-call-sentiment to $ENVIRONMENT..."

cd "$TERRAFORM_DIR"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Create tfvars file if not exists
TFVARS_FILE="$TERRAFORM_DIR/$ENVIRONMENT.tfvars"
if [ ! -f "$TFVARS_FILE" ]; then
    echo "Creating $TFVARS_FILE..."
    cat > "$TFVARS_FILE" << EOF
environment = "$ENVIRONMENT"
aws_region  = "eu-central-2"

# OpenSearch configuration
opensearch_instance_type   = "t3.small.search"
opensearch_instance_count  = 2
opensearch_ebs_volume_size = 20
opensearch_master_user     = "admin"
opensearch_master_password = "ChangeMe123!"

# Retention
retention_days     = 90
log_retention_days = 30

# Monitoring (optional)
alarm_email = ""
EOF
    echo "Created $TFVARS_FILE - please update with your values"
fi

# Run Terraform action
case $ACTION in
    plan)
        terraform plan -var-file="$TFVARS_FILE"
        ;;
    apply)
        terraform apply -var-file="$TFVARS_FILE" -auto-approve

        # Update Lambda code
        if [ -f "$PROJECT_DIR/lambda.zip" ]; then
            echo "Updating Lambda functions..."
            FUNCTIONS=$(terraform output -json lambda_functions | jq -r 'to_entries[] | .value')
            for fn in $FUNCTIONS; do
                echo "Updating $fn..."
                aws lambda update-function-code \
                    --function-name "$fn" \
                    --zip-file "fileb://$PROJECT_DIR/lambda.zip" \
                    --region "$(terraform output -raw aws_region 2>/dev/null || echo 'eu-central-2')" \
                    > /dev/null
            done
        fi

        echo ""
        echo "Deployment complete!"
        echo "API Endpoint: $(terraform output -raw api_endpoint)"
        echo "OpenSearch Dashboard: $(terraform output -raw opensearch_dashboard_url)"
        ;;
    destroy)
        terraform destroy -var-file="$TFVARS_FILE" -auto-approve
        echo "Infrastructure destroyed."
        ;;
esac
