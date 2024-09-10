/* The IoT policy permits devices to access the IoT Core MQTT broker. */
resource "aws_iot_policy" "iot_policy" {
  name = var.iot_policy

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iot:*"
        Resource = "*"
      },
    ]
  })
}

/* The IAM Role allows the template (defined below) permissions to create
   Certificate resources and attach policies on the IoT Core service. */
resource "aws_iam_role" "iam_role" {
  name = var.jitp_iam_role

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Principal = {
          Service = ["iot.amazonaws.com"]
        }
      }
    ]
  })
}

/* Attach IAM policy to the IAM role. */
resource "aws_iam_role_policy_attachment" "iot_full_access_attach" {
role       = aws_iam_role.iam_role.name
policy_arn = "arn:aws:iam::aws:policy/AWSIoTConfigAccess"
}

/* The IoT Provisioning Template is of type JITP (just-in-time Provisioning).
   When a device contacts the server, assuming its device certificate is
   signed by the CA Certificate (defined below), the template is defined to
   automatically create a Certificate resource and attach the IoT Policy
   defined above, allowing it to access the MQTT server. */
resource "aws_iot_provisioning_template" "provisioning_template" {
  name                  = var.provisioning_template
  provisioning_role_arn = aws_iam_role.iam_role.arn
  type                  = "JITP"
  enabled               = true

  template_body = jsonencode({
    Parameters = {
      "AWS::IoT::Certificate::Id" = {Type = "String"}
    }
    Resources = {
      certificate = {
        Type = "AWS::IoT::Certificate"
        Properties = {
          CertificateId = { Ref = "AWS::IoT::Certificate::Id" }
          Status = "Active"
        }
      }
      policy_iar-jitp-iot-policy = {
        Type = "AWS::IoT::Policy"
        Properties = {
          PolicyName = var.iot_policy
        }
      }
    }
  })
}

/* This certificate is attached to the template defined above. The template
   will check whether device certificates have been signed by the holder of
   the private key associated with this X509 certificate pem. */
resource "aws_iot_ca_certificate" "ca_certificate" {
  depends_on = [ aws_iot_provisioning_template.provisioning_template ]
  active                  = true
  ca_certificate_pem      = file(var.intermediate_cert)
  allow_auto_registration = true
  certificate_mode        = "SNI_ONLY" /* No verification cert required */
  registration_config {
    template_name = var.provisioning_template
  }
}
