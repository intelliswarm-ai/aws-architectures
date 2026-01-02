################################################################################
# EC2 Module Outputs
################################################################################

output "asg_name" {
  description = "Name of the Auto Scaling Group"
  value       = aws_autoscaling_group.processor.name
}

output "asg_arn" {
  description = "ARN of the Auto Scaling Group"
  value       = aws_autoscaling_group.processor.arn
}

output "launch_template_id" {
  description = "ID of the launch template"
  value       = aws_launch_template.processor.id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.processor.arn
}

output "processor_security_group_id" {
  description = "ID of the processor security group"
  value       = aws_security_group.processor.id
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "scale_out_policy_arn" {
  description = "ARN of the scale-out policy"
  value       = aws_autoscaling_policy.scale_out.arn
}

output "scale_in_policy_arn" {
  description = "ARN of the scale-in policy"
  value       = aws_autoscaling_policy.scale_in.arn
}
