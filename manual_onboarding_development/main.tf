/* The device certificate is uploaded to a Certificate resource. */
resource "aws_iot_certificate" "device_certificate" {
  active          = true
  certificate_pem = file("device-certificate.pem")
}

/* The Policy defines permissions to access the IoT Core MQTT broker. */
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

/* Attach the Policy to the Certificate resource. */
resource "aws_iot_policy_attachment" "attach_device_cert_to_policy" {
  policy = aws_iot_policy.iot_policy.name
  target = aws_iot_certificate.device_certificate.arn
}
