################################################################################
# IAM Module Outputs
################################################################################

output "ec2_role_arn" {
  description = "ARN of the EC2 processor role"
  value       = aws_iam_role.ec2_processor.arn
}

output "ec2_role_name" {
  description = "Name of the EC2 processor role"
  value       = aws_iam_role.ec2_processor.name
}

output "ec2_instance_profile_arn" {
  description = "ARN of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_processor.arn
}

output "ec2_instance_profile_name" {
  description = "Name of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_processor.name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda.name
}
