####################################################################################################
# Terraform apply routine

resource "null_resource" "register_ca_certificate" {
  provisioner "local-exec" {
    when    = create
    command = <<EOT
    aws iot register-ca-certificate --ca-certificate file://${var.intermediate_cert} \
    --certificate-mode SNI_ONLY --region ${var.aws_region} --set-as-active \
    --allow-auto-registration | jq -r .certificateId > certificateId.txt
    EOT
  }
}

resource "aws_iam_role" "jitp_iam_role" {
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

resource "aws_iam_role_policy_attachment" "iot_things_registration_policy" {
  depends_on = [aws_iam_role.jitp_iam_role]
  role       = aws_iam_role.jitp_iam_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSIoTThingsRegistration"
}

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

resource "null_resource" "create_provisioning_template" {
  depends_on = [
    aws_iot_policy.iot_policy,
    null_resource.register_ca_certificate,
    aws_iam_role_policy_attachment.iot_things_registration_policy,
    aws_iam_role.jitp_iam_role
  ]

  # Sleep for 10s to allow for iot_things_registration_policy to take effect
  provisioner "local-exec" {
    when    = create
    command = <<EOT
    sleep 10
    aws iot create-provisioning-template --template-name terraform-jitp-provisioning-template \
    --type JITP --provisioning-role-arn 'arn:aws:iam::${var.aws_account_num}:role/${var.jitp_iam_role}' \
    --template-body file://jitp-provisioning-template.json --enabled --region ${var.aws_region}
    EOT
  }
}

resource "null_resource" "attach_ca_cert_to_template" {
  depends_on = [null_resource.create_provisioning_template, null_resource.register_ca_certificate]
  provisioner "local-exec" {
    when    = create
    command = <<EOT
    aws iot update-ca-certificate --certificate-id $(cat certificateId.txt) \
    --registration-config "templateName=terraform-jitp-provisioning-template" --region eu-west-2
    EOT
  }
}

resource "aws_accessanalyzer_analyzer" "analyzer" {
  analyzer_name = "jitp-analyzer"
  depends_on    = [null_resource.create_provisioning_template]
}

####################################################################################################
# Terraform destroy routine

resource "null_resource" "delete_provisioning_template" {
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
    aws iot delete-provisioning-template --template-name terraform-jitp-provisioning-template \
    --region eu-west-2
    EOT
  }
}

resource "null_resource" "deactivate_ca_certificate" {
  depends_on = [null_resource.delete_ca_certificate]
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
    aws iot update-ca-certificate --certificate-id $(cat certificateId.txt) \
    --region eu-west-2 --new-status 'INACTIVE'
    EOT
  }
}

resource "null_resource" "delete_ca_certificate" {
  depends_on = [null_resource.delete_provisioning_template]
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
    aws iot delete-ca-certificate --certificate-id $(cat certificateId.txt) --region eu-west-2
    EOT
  }
}
