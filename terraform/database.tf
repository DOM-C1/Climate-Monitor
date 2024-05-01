data "aws_db_subnet_group" "public_subnet_group" {
    name = "public_subnet_group"
}


data "aws_vpc" "cohort_10_vpc" {
    id = "vpc-0c4f01396d92e1cc7"
}

resource "aws_db_instance" "climate-db" {
    allocated_storage = 10
    db_name = "postgres"
    identifier = "c10-climate-db-terraform"
    engine = "postgres"
    engine_version = "16.1"
    instance_class = "db.t3.micro"
    publicly_accessible = true
    performance_insights_enabled = false
    skip_final_snapshot = true
    db_subnet_group_name = data.aws_db_subnet_group.public_subnet_group.name
    vpc_security_group_ids = [aws_security_group.rds-security-group.id]
    username = var.DB_USER
    password = var.DB_PASSWORD
}

resource "aws_security_group" "rds-security-group" {
    name = "c10-climate-db-sg"
    description = "Allows inbound Postgres access"
    vpc_id = data.aws_vpc.cohort_10_vpc.id
    
    ingress {
        cidr_blocks = ["0.0.0.0/0"]
        from_port = 5432
        protocol = "tcp"
        to_port = 5432
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
        ipv6_cidr_blocks = ["::/0"]
    }
}
