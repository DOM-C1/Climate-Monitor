data "aws_iam_policy_document" "daily-report-lambda-role-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "daily-report-lambda-role" {
  name               = "c10-climate-terraform-lambda-role-daily-report"
  assume_role_policy = data.aws_iam_policy_document.daily-report-lambda-role-policy.json
}

data "aws_ecr_repository" "daily-report-repo" {
  name = "climate-monitoring_daily_report"
}

data "aws_ecr_image" "daily-report-image" {
  repository_name = data.aws_ecr_repository.daily-report-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-daily-report-terraform" {
    role = aws_iam_role.daily-report-lambda-role.arn
    function_name = "c10-climate-daily-report-terraform"
    package_type = "Image"
    image_uri = data.aws_ecr_image.daily-report-image.image_uri
    environment {
        variables = {
          AWS_KEY = var.AWS_KEY,
          AWS_SKEY = var.AWS_SKEY,
          DB_HOST = var.DB_HOST,
          DB_NAME = var.DB_NAME,
          DB_PASSWORD = var.DB_PASSWORD,
          DB_PORT = var.DB_PORT,
          DB_USER = var.DB_USER
        }
      
    }
    timeout = 360
}