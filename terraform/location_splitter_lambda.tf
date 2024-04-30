data "aws_iam_policy_document" "location-splitter-lambda-role-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "location-splitter-lambda-role" {
  name               = "c10-climate-terraform-lambda-role-location-splitter"
  assume_role_policy = data.aws_iam_policy_document.location-splitter-lambda-role-policy.json
}

data "aws_ecr_repository" "location-splitter-repo" {
  name = "c10-climate-location-splitter"
}

data "aws_ecr_image" "location-splitter-image" {
  repository_name = data.aws_ecr_repository.location-splitter-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-location-splitter-terraform" {
    role = aws_iam_role.location-splitter-lambda-role.arn
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