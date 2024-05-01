provider "aws" {
  region = "eu-west-2"
}

resource "aws_ecs_cluster" "example" {
  name = "climate-monitor-cluster"
}

resource "aws_ecs_task_definition" "climate_monitor" {
  family                   = "Climate-Monitor_website"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  cpu                      = "1024"
  memory                   = "3072"

  container_definitions = jsonencode([
    {
      name        = "Climate-Monitor_website"
      image       = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/climate-monitoring_website:latest"
      cpu         = 0
      essential   = true
      environment = [
        {
          name  = "DB_NAME"
          value = "weather"
        },
        {
          name  = "API_KEY"
          value = "24uzav7sbcW3MTOfNdd8aQ==hK414Svr98qyUljV"
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
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        },
        {
          containerPort = 5000
          hostPort      = 5000
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/Climate-Monitor_website"
          "awslogs-region"        = "eu-west-2"
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group"  = "true"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "climate_monitor_service" {
  name            = "Climate-Monitor_Service"
  cluster         = aws_ecs_cluster.example.id
  task_definition = aws_ecs_task_definition.climate_monitor.arn
  desired_count   = 1

  launch_type = "FARGATE"

  network_configuration {
    subnets          = ["subnet-xxx", "subnet-yyy"]
    security_groups  = ["sg-xxxx"]
    assign_public_ip = true
  }

  depends_on = [
    aws_ecs_task_definition.climate_monitor
  ]
}
