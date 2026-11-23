resource "aws_db_instance" "exemplo" {
  identifier          = "rds-exemplo"
  engine              = "mysql"
  publicly_accessible = true
}
