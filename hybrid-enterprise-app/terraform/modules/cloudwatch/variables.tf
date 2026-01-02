variable "environment" {
  description = "Environment name"
  type        = string
}

variable "application_name" {
  description = "Application name"
  type        = string
}

variable "eb_environment" {
  description = "Elastic Beanstalk environment name"
  type        = string
}

variable "alarm_email" {
  description = "Email for alarms"
  type        = string
  default     = ""
}
