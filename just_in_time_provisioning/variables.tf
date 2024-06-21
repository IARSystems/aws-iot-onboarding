variable "aws_region" {
  description = "The AWS region in which you would like to create resources"
  type        = string
  default     = "eu-west-2"
}

variable "jitp_iam_role" {
  description = "The role that the provisioning template will assume to register devices"
  type        = string
  default     = "terraform-jitp-iam-role"
}

variable "iot_policy" {
  description = "IoT policy to be attached to registered devices"
  type        = string
  default     = "terraform-jitp-iot-policy"
}

variable "aws_account_num" {
  type        = string
  nullable    = false
  description = "\nYour unique AWS account number."
}

variable "intermediate_cert" {
  type        = string
  nullable    = false
  description = "\nThe Intermediate certificate that signed your device certificates (.pem format)."
}
