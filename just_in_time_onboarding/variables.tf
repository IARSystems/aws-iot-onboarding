variable "aws_region" {
  description = "The AWS region in which you would like to create resources"
  type        = string
  default     = "eu-west-2"
}

variable "jitp_iam_role" {
  description = "The role that the provisioning template will assume to register devices"
  type        = string
  default     = "iar-jitp-iam-role"
}

variable "iot_policy" {
  description = "IoT policy to be attached to registered devices"
  type        = string
  default     = "iar-jitp-iot-policy"
}

variable "provisioning_template" {
  description = "Provisioning template defining actions to take during TLS connection"
  type        = string
  default     = "iar-jitp-provisioning-template"
}

variable "intermediate_cert" {
  type        = string
  nullable    = false
  description = "Path to the X509 certificate .pem file corresponding with the private key that signed each device certificate"
}
