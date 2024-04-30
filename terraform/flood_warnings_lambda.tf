data "aws_iam_policy_document" "flood-warnings-lambda-role-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "flood-warnings-lambda-role" {
  name               = "c10-climate-terraform-lambda-role-flood-warnings"
  assume_role_policy = data.aws_iam_policy_document.flood-warnings-lambda-role-policy.json
}

data "aws_ecr_repository" "flood-warnings-repo" {
  name = "c10-flood-warnings"
}

data "aws_ecr_image" "flood-warnings-image" {
  repository_name = data.aws_ecr_repository.flood-warnings-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-flood-warnings-terraform" {
    role = aws_iam_role.flood-warnings-lambda-role.arn
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