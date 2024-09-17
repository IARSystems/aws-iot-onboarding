variable "aws_region" {
  description = "The AWS region in which you would like to create resources"
  type        = string
  default     = "eu-west-2"
}

variable "iot_policy" {
  description = "IoT policy to be attached to registered devices"
  type        = string
  default     = "manual-dev-policy"
}
