# Create deployment package zip file of the lambda function code.
resource "null_resource" "deployment_package" {
  triggers = {
    timestamp = timestamp()
  }
  provisioner "local-exec" {
    command = "./create_pkg.sh"
  }
}

variable "public_key" {
  type     = string
  nullable = false
  description = "The public key used to validate production record signatures"
}

# Create a lambda function and upload the deployment package zip file.
resource "aws_lambda_function" "production_record_processing" {
  function_name = var.lambda_function_name
  handler       = "runtimescript.lambda_handler"
  runtime       = "python3.10"
  timeout       = 15
  role          = aws_iam_role.production_record_processing_role.arn
  filename      = "deployment_package.zip"
  lifecycle {
    replace_triggered_by = [
      null_resource.deployment_package
    ]
  }
  tracing_config {
    mode = "Active"
  }
  environment {
    variables = {
      PUBLIC_KEY=var.public_key,
      THING_GROUP_NAME=var.thing_group_name
    }
  }
}

# Define an IAM Role to access the Lambda and IoT services.
resource "aws_iam_role" "production_record_processing_role" {
  name = "ProductionRecordProcessingRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "iot.amazonaws.com"
          ]
        }
      },
    ]
  })
}

# Create IAM policies required by the solution.
resource "aws_iam_policy" "iot_onboarding_iam_polices" {
  name        = "IoTOnboardingIAMPolicies"
  description = "Policy to allow iam:PassRole"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = [
          "s3:GetObject",
          "s3:DeleteObject",
          "iot:CreateThing",
          "iot:DescribeThingGroup",
          "iot:CreateThingGroup",
          "iot:AddThingToThingGroup",
          "iot:RegisterCertificateWithoutCA",
          "iot:AttachThingPrincipal"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
    ]
  })
}

# Attach the IAM policies to the IAM Role.
resource "aws_iam_role_policy_attachment" "attach_iot_onboarding_iam_polices" {
  role       = aws_iam_role.production_record_processing_role.name
  policy_arn = aws_iam_policy.iot_onboarding_iam_polices.arn
}

resource "aws_iam_role_policy_attachment" "attach_lambda_execution_policy" {
  role       = aws_iam_role.production_record_processing_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Define an S3 Bucket to hold production record files.
resource "aws_s3_bucket" "iot_onboarding_bucket" {
  bucket        = var.s3_bucket_name
  force_destroy = true
}

resource "aws_accessanalyzer_analyzer" "iot_bucket_analyzer" {
  analyzer_name = "IoTOnboardingBucketAnalyzer"
  depends_on    = [aws_s3_bucket.iot_onboarding_bucket]
}

resource "aws_s3_bucket_versioning" "iot_bucket_versioning" {
  bucket = aws_s3_bucket.iot_onboarding_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "iot_bucket_acl_ownership" {
  bucket = aws_s3_bucket.iot_onboarding_bucket.id
  rule {
    object_ownership = "ObjectWriter"
  }
}

resource "aws_s3_bucket_acl" "iot_bucket_acl" {
  bucket = aws_s3_bucket.iot_onboarding_bucket.id
  acl    = "private"

  # Must change default ownership controls to define acl
  depends_on = [aws_s3_bucket_ownership_controls.iot_bucket_acl_ownership]
}

# Logging bucket for main onboarding bucket
resource "aws_s3_bucket" "log_bucket" {
  bucket        = var.s3_log_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "log_bucket_versioning" {
  bucket = aws_s3_bucket.log_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "log_bucket_acl_ownership" {
  bucket = aws_s3_bucket.log_bucket.id
  rule {
    object_ownership = "ObjectWriter"
  }
}

resource "aws_s3_bucket_acl" "log_bucket_acl" {
  bucket = aws_s3_bucket.log_bucket.id
  acl    = "log-delivery-write"

  # Must change default ownership controls to define acl
  depends_on = [aws_s3_bucket_ownership_controls.log_bucket_acl_ownership]
}

resource "aws_s3_bucket_logging" "bucket_logging" {
  bucket        = aws_s3_bucket.iot_onboarding_bucket.id
  target_bucket = aws_s3_bucket.log_bucket.id
  target_prefix = "log/"
}

# Create a Lambda Function Trigger for "new object created in the S3 bucket".
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.iot_onboarding_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.production_record_processing.arn
    events              = ["s3:ObjectCreated:*"]
  }
  lifecycle {
    replace_triggered_by = [
      aws_lambda_function.production_record_processing
    ]
  }
}

# Add permissions for S3 bucket to trigger the Lambda Function.
resource "aws_lambda_permission" "allow_bucket" {
  statement_id = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.production_record_processing.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.iot_onboarding_bucket.arn
  lifecycle {
    replace_triggered_by = [
      aws_lambda_function.production_record_processing
    ]
  }
}
