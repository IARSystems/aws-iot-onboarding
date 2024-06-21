variable "aws_region" {
  description = "The AWS region in which you would like to create resources"
  type        = string
  default     = "eu-west-2"
}

variable "s3_bucket_name" {
  description = "The name of the bucket to be created on the AWS S3 service"
  type        = string
  default     = "iar-iot-onboarding-bucket"
}

variable "s3_log_bucket_name" {
  description = "The name of the logging bucket to be created on the AWS S3 service"
  type        = string
  default     = "iar-iot-onboarding-log-bucket"
}

variable "lambda_function_name" {
  description = "The name of the lambda function to be created on the AWS Lambda service"
  type        = string
  default     = "iar-production-record-processing"
}

variable "thing_group_name" {
  description = "The name of Thing Group in which Things will be created by the Lambda function"
  type        = string
  default     = "iar-thing-group"
}

variable "public_key" {
  type        = string
  nullable    = false
  description = "\nThe public part of the key used to sign your production records (in hex string format)."
}

variable "iot_policy" {
  description = "IoT policy to be attached to registered devices"
  type        = string
  default     = "iar-thing-group-policy"
}
