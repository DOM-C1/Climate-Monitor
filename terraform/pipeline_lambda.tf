data "aws_iam_policy_document" "pipeline-lambda-role-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "pipeline-lambda-role" {
  name               = "c10-climate-terraform-lambda-role-pipeline"
  assume_role_policy = data.aws_iam_policy_document.pipeline-lambda-role-policy.json
}

data "aws_ecr_repository" "pipeline-repo" {
  name = "c10-climate-pipeline"
}

data "aws_ecr_image" "pipeline-image" {
  repository_name = data.aws_ecr_repository.pipeline-repo.name
  image_tag       = "latest"
}

resource "aws_lambda_function" "c10-climate-pipeline-terraform" {
    role = aws_iam_role.pipeline-lambda-role.arn
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