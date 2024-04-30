data "aws_iam_policy_document" "email-alert-lambda-role-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "email-alert-lambda-role" {
  name               = "c10-climate-terraform-lambda-role-email-alert"
  assume_role_policy = data.aws_iam_policy_document.email-alert-lambda-role-policy.json
}

data "aws_ecr_repository" "email-alert-repo" {
  name = "c10-climate-emails"
}

data "aws_ecr_image" "email-alert-image" {
  repository_name = data.aws_ecr_repository.email-alert-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-email-alert-terraform" {
    role = aws_iam_role.email-alert-lambda-role.arn
    function_name = "c10-climate-email-alert-terraform"
    package_type = "Image"
    image_uri = data.aws_ecr_image.email-alert-image.image_uri
    environment {
        variables = {
          DB_HOST = var.DB_HOST,
          DB_NAME = var.DB_NAME,
          DB_PASSWORD = var.DB_PASSWORD,
          DB_PORT = var.DB_PORT,
          DB_USER = var.DB_USER,
          REGION = var.REGION,
          AIR_QUALITY_TABLE = var.AIR_QUALITY_TABLE,
          FLOOD_WARNING_TABLE = var.FLOOD_WARNING_TABLE,
          SENDER_EMAIL = var.SENDER_EMAIL,
          WEATHER_WARNING_TABLE = var.WEATHER_WARNING_TABLE
        }
      
    }
    timeout = 15
}