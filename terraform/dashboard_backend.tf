data "aws_ecr_repository" "backend-repo" {
  name = "climate-monitoring_website"
}

data "aws_ecr_image" "backend-image" {
  repository_name = data.aws_ecr_repository.backend-repo.name
  image_tag       = "latest"
}

resource "aws_ecs_task_definition" "backend-task-definition" {
  family                   = "c10-climate-backend-terraform"
  network_mode             = "awsvpc"
  execution_role_arn       = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::129033205317:role/ecs_role"
  cpu                      = "1024"
  memory                   = "3072"
  requires_compatibilities = ["FARGATE"]

  container_definitions = jsonencode([
    {
      name         = "c10-climate-backend-ecr"
      image        = aws_ecr_image.backend-image.image_uri
      cpu          = 0
      essential    = true
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DB_NAME"
          value = "${var.DB_NAME}"
        },
        {
          name  = "DB_HOST"
          value = "${aws_db_instance.climate-db.address}"
        },
        {
          name  = "DB_PORT"
          value = "${var.DB_PORT}"
        },
        {
          name  = "DB_USER"
          value = "${var.DB_USER}"
        },
        {
          name  = "DB_PASSWORD"
          value = "${var.DB_PASSWORD}"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/c10-climate-backend"
          "awslogs-region"        = "${var.REGION}"
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

resource "aws_security_group" "backend-security-group" {
    name = "c10-climate-backend-sg"
    description = "c10-climate-backend-sg"
    vpc_id = data.aws_vpc.cohort_10_vpc.id
    
    ingress {
        cidr_blocks = ["0.0.0.0/0"]
        from_port = 5000
        protocol = "tcp"
        to_port = 5000
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
        ipv6_cidr_blocks = ["::/0"]
    }
}

resource "aws_ecs_service" "backend-service" {
  name            = "c10-climate-backend-service-terraform"
  cluster         = data.aws_ecs_cluster.ecs-cluster.id
  task_definition = aws_ecs_task_definition.backend-task-definition.arn
  desired_count   = 1

  network_configuration {
    subnets = ["subnet-0f1bc89d0670672b5"]
    security_groups = [aws_security_group.dashboard-security-group.id]
    assign_public_ip = true
  }
}