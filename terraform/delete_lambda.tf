data "aws_iam_policy_document" "delete-lambda-role-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "delete-lambda-role" {
  name               = "c10-climate-terraform-lambda-role-delete"
  assume_role_policy = data.aws_iam_policy_document.delete-lambda-role-policy.json
}

data "aws_ecr_repository" "delete-repo" {
  name = "c10-climate-delete"
}

data "aws_ecr_image" "delete-image" {
  repository_name = data.aws_ecr_repository.delete-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-delete-terraform" {
    role = aws_iam_role.delete-lambda-role.arn
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