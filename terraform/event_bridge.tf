
# The permission policy
data "aws_iam_policy_document" "eventbridge-permissions-policy" {
  statement {
    effect = "Allow"

    resources = ["*"]
 
    actions = ["states:StartExecution"]
  }
}

# The trust policy
data "aws_iam_policy_document" "eventbridge-trust-policy" {
  statement {
    effect = "Allow"

    principals {
       type        = "Service"
       identifiers = ["scheduler.amazonaws.com"]
     }
 
    actions = ["sts:AssumeRole"]
  }
}


# The role
resource "aws_iam_role" "eventbridge-role" {
  name               = "c10-gamma-terraform-eventbrige-role-pipeline"
  assume_role_policy = data.aws_iam_policy_document.eventbridge-trust-policy.json
  inline_policy {
    name = "c10-gamma-inline-step-function"
    policy = data.aws_iam_policy_document.eventbridge-permissions-policy.json
  }
}


resource "aws_scheduler_schedule" "c10-climate-delete-schedule-terraform" {
    name = "c10-climate-delete-schedule-terraform"
    flexible_time_window {
    mode = "OFF"
    }
    schedule_expression = "cron(0 * * * ? *)"
    schedule_expression_timezone = "Europe/London"
    target {
    arn      = aws_lambda_function.c10-climate-delete.arn
    role_arn = aws_iam_role.eventbridge-role.arn
    }
}

resource "aws_scheduler_schedule" "c10-climate-step_function-terraform" {
    name = "c10-climate-step_function-terraform"
    flexible_time_window {
    mode = "OFF"
    }
    schedule_expression = "cron(*/15 * * * ? *)"
    schedule_expression_timezone = "Europe/London"
    target {
    arn      = aws_sfn_state_machine.c10-climate-step-function-pipeline.arn
    role_arn = aws_iam_role.eventbridge-role.arn
    }
}

resource "aws_scheduler_schedule" "c10-climate-daily-report-terraform" {
    name = "c10-climate-daily-report-terraform"
    flexible_time_window {
    mode = "OFF"
    }
    schedule_expression = "cron(0 7 * * ? *)"
    schedule_expression_timezone = "Europe/London"
    target {
    arn      = aws_sfn_state_machine.c10-climate-daily-report.arn
    role_arn = aws_iam_role.eventbridge-role.arn
    }
}