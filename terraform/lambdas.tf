data "aws_iam_policy_document" "lambda-role-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda-role" {
  name               = "c10-climate-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda-role-policy.json
}

data "aws_ecr_repository" "daily-report-repo" {
  name = "climate-monitoring_daily_report"
}

data "aws_ecr_image" "daily-report-image" {
  repository_name = data.aws_ecr_repository.daily-report-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-daily-report" {
    role = aws_iam_role.lambda-role.arn
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

data "aws_ecr_repository" "delete-repo" {
  name = "c10-climate-delete"
}

data "aws_ecr_image" "delete-image" {
  repository_name = data.aws_ecr_repository.delete-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-delete" {
    role = aws_iam_role.lambda-role.arn
    function_name = "c10-climate-delete-terraform"
    package_type = "Image"
    image_uri = data.aws_ecr_image.delete-image.image_uri
    environment {
        variables = {
          DB_HOST = var.DB_HOST,
          DB_NAME = var.DB_NAME,
          DB_PASSWORD = var.DB_PASSWORD,
          DB_PORT = var.DB_PORT,
          DB_USER = var.DB_USER,
          REGION = var.REGION
        }
      
    }
    timeout = 10
}

data "aws_ecr_repository" "email-alert-repo" {
  name = "c10-climate-emails"
}

data "aws_ecr_image" "email-alert-image" {
  repository_name = data.aws_ecr_repository.email-alert-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-email-alert" {
    role = aws_iam_role.lambda-role.arn
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

data "aws_ecr_repository" "flood-warnings-repo" {
  name = "c10-flood-warnings"
}

data "aws_ecr_image" "flood-warnings-image" {
  repository_name = data.aws_ecr_repository.flood-warnings-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-flood-warnings" {
    role = aws_iam_role.lambda-role.arn
    function_name = "c10-climate-flood-warnings-terraform"
    package_type = "Image"
    image_uri = data.aws_ecr_image.flood-warnings-image.image_uri
    environment {
        variables = {
          DB_HOST = var.DB_HOST,
          DB_NAME = var.DB_NAME,
          DB_PASSWORD = var.DB_PASSWORD,
          DB_PORT = var.DB_PORT,
          DB_USER = var.DB_USER
        }
      
    }
    timeout = 60
}

data "aws_ecr_repository" "location-splitter-repo" {
  name = "c10-climate-location-splitter"
}

data "aws_ecr_image" "location-splitter-image" {
  repository_name = data.aws_ecr_repository.location-splitter-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-location-splitter" {
    role = aws_iam_role.lambda-role.arn
    function_name = "c10-climate-location-splitter-terraform"
    package_type = "Image"
    image_uri = data.aws_ecr_image.location-splitter-image.image_uri
    environment {
        variables = {
          DB_HOST = var.DB_HOST,
          DB_NAME = var.DB_NAME,
          DB_PASSWORD = var.DB_PASSWORD,
          DB_PORT = var.DB_PORT,
          DB_USER = var.DB_USER
        }
      
    }
    timeout = 3
}

data "aws_ecr_repository" "pipeline-repo" {
  name = "c10-climate-pipeline"
}

data "aws_ecr_image" "pipeline-image" {
  repository_name = data.aws_ecr_repository.pipeline-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-pipeline" {
    role = aws_iam_role.lambda-role.arn
    function_name = "c10-climate-pipeline-terraform"
    package_type = "Image"
    image_uri = data.aws_ecr_image.pipeline-image.image_uri
    environment {
        variables = {
          API_KEY = var.API_KEY,
          DB_HOST = var.DB_HOST,
          DB_NAME = var.DB_NAME,
          DB_PASSWORD = var.DB_PASSWORD,
          DB_PORT = var.DB_PORT,
          DB_USER = var.DB_USER
        }
      
    }
    timeout = 600
}