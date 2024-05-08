data "aws_ecr_repository" "dashboard-repo" {
  name = "climate-monitoring_daily_report"
}

data "aws_ecr_image" "dashboard-image" {
  repository_name = data.aws_ecr_repository.dashboard-repo.name
  image_tag       = "latest"
}

resource "aws_ecs_task_definition" "dashboard-task-definition" {
  family                   = "c10-climate-dashboard-terraform"
  network_mode             = "awsvpc"
  execution_role_arn       = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::129033205317:role/ecs_role"
  cpu                      = "1024"
  memory                   = "3072"
  requires_compatibilities = ["FARGATE"]

  container_definitions = jsonencode([
    {
      name         = "c10-climate-dashboard-ecr"
      image        = aws_ecr_image.dashboard-image.image_uri
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
        },
        {
          name = "HASH_KEY"
          value = "${var.HASH_KEY}"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/c10-climate-dashboard"
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

resource "aws_security_group" "dashboard-security-group" {
    name = "c10-climate-dashboard-sg"
    description = "c10-climate-dashboard-sg"
    vpc_id = data.aws_vpc.cohort_10_vpc.id
    
    ingress {
        cidr_blocks = ["0.0.0.0/0"]
        from_port = 8501
        protocol = "tcp"
        to_port = 8501
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
        ipv6_cidr_blocks = ["::/0"]
    }
}

data "aws_ecs_cluster" "ecs-cluster" {
    cluster_name = "c10-ecs-cluster"
}

resource "aws_ecs_service" "dashboard-service" {
  name            = "c10-climate-dashboard-service-terraform"
  cluster         = data.aws_ecs_cluster.ecs-cluster.id
  task_definition = aws_ecs_task_definition.dashboard-task-definition.arn
  desired_count   = 1

  network_configuration {
    subnets = ["subnet-0f1bc89d0670672b5"]
    security_groups = [aws_security_group.dashboard-security-group.id]
    assign_public_ip = true
  }
}