variable "aws_region" {
  description = "The AWS region in which you would like to create resources."
  type        = string
  default     = "eu-west-2"
}

variable "s3_bucket" {
  description = "The name of the bucket to be created on the AWS S3 service."
  type        = string
  default     = "iar-manual-prod-bucket"
}

variable "iam_role" {
  description = "The name of the IAM Role to attach to the Lambda function."
  type        = string
  default     = "iar-manual-prod-iam-role"
}

variable "iam_policy" {
  description = "Policy to be attached to the IAM Role."
  type        = string
  default     = "iar-manual-prod-iam-policy"
}

variable "access_analyzer" {
  description = "Access analyzer to track access to S3 bucket."
  type        = string
  default     = "iar-manual-prod-access-analyzer"
}

variable "s3_log_bucket" {
  description = "The name of the logging bucket to be created on the AWS S3 service."
  type        = string
  default     = "iar-manual-prod-log-bucket"
}

variable "lambda_function" {
  description = "The name of the Lambda function to be created on the AWS Lambda service."
  type        = string
  default     = "iar-manual-prod-lambda-function"
}

variable "thing_group" {
  description = "The name of Thing Group in which Things will be created by the Lambda function."
  type        = string
  default     = "iar-manual-prod-thing-group"
}

variable "public_key" {
  type        = string
  nullable    = false
  description = "\nThe public part of the key used to sign your production records (in hex string format)."
}

variable "iot_policy" {
  description = "Policy to be attached to the Thing Group."
  type        = string
  default     = "iar-manual-prod-iot-policy"
}
