resource "aws_db_instance" "exemplo" {
  identifier          = "rds-exemplo"
  engine              = "postgres"
  publicly_accessible = false
}
