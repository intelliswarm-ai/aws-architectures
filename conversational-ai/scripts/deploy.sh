#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_DIR/terraform"

# Default values
ENVIRONMENT="dev"
AWS_REGION="eu-central-2"
DESTROY=false
AUTO_APPROVE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        --destroy)
            DESTROY=true
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"

cd "$TERRAFORM_DIR"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init -upgrade

# Create tfvars file
cat > terraform.tfvars <<EOF
environment = "$ENVIRONMENT"
aws_region  = "$AWS_REGION"
EOF

if [ "$DESTROY" = true ]; then
    echo "Destroying infrastructure..."
    if [ "$AUTO_APPROVE" = true ]; then
        terraform destroy -auto-approve
    else
        terraform destroy
    fi
else
    # Build Lambda package first
    echo "Building Lambda package..."
    "$SCRIPT_DIR/build.sh"

    # Plan
    echo "Planning infrastructure changes..."
    terraform plan -out=tfplan

    # Apply
    echo "Applying infrastructure changes..."
    if [ "$AUTO_APPROVE" = true ]; then
        terraform apply -auto-approve tfplan
    else
        terraform apply tfplan
    fi

    # Show outputs
    echo ""
    echo "Deployment complete! Outputs:"
    terraform output

    # Update Lambda function code
    echo ""
    echo "Updating Lambda function code..."
    FUNCTION_NAME=$(terraform output -raw fulfillment_lambda_arn | sed 's/.*function://')
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$PROJECT_DIR/build/lambda.zip" \
        --region "$AWS_REGION" || echo "Note: Lambda update may require additional permissions"
fi

echo ""
echo "Done!"
