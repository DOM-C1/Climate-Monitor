resource "null_resource" "db_setup" {
    provisioner "local-exec" {
        command = "echo DB_HOST=$DB_HOST >> .env"
        environment = {
            DB_HOST = aws_db_instance.climate-db.address
        }
    interpreter = ["bash", "-c"]
  }
}
