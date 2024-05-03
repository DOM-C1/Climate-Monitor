resource "aws_ecs_task_definition" "c10_climate_dashboard" {
  family                   = "c10-climate-dashboard"
  network_mode             = "awsvpc"
  execution_role_arn       = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::129033205317:role/ecs_role"
  cpu                      = "1024"
  memory                   = "3072"
  requires_compatibilities = ["FARGATE"]

  container_definitions = jsonencode([
    {
      name         = "c10-climate-dashboard-ecr"
      image        = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c10-climate-dashboard-ecr"
      cpu          = 0
      essential    = true
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DB_NAME"
          value = "weather"
        },
        {
          name  = "DB_HOST"
          value = "climate-monitoring-database.c57vkec7dkkx.eu-west-2.rds.amazonaws.com"
        },
        {
          name  = "DB_PORT"
          value = "5432"
        },
        {
          name  = "DB_USER"
          value = "postgres"
        },
        {
          name  = "DB_PASSWORD"
          value = "Thund3r!"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/c10-climate-dashboard"
          "awslogs-region"        = "eu-west-2"
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group"  = "true"
        }
      }
    }
  ])

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }
}