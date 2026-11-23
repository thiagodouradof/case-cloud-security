resource "aws_db_instance" "pagamentos" {
  identifier                  = "rds-pagamentos-prd"
  engine                      = "postgres"
  engine_version              = "16.3"
  instance_class              = "db.t3.medium"
  allocated_storage           = 50
  db_name                     = "pagamentos"
  username                    = "app_admin"
  manage_master_user_password = true
  db_subnet_group_name        = "subnets-privadas-dados"
  vpc_security_group_ids      = ["sg-0aa11bb22cc33dd44"]
  publicly_accessible         = false
  storage_encrypted           = true
  backup_retention_period     = 7
  deletion_protection         = true
  skip_final_snapshot         = false

  tags = {
    Ambiente = "producao"
  }
}

resource "aws_db_instance" "cadastro" {
  identifier                  = "rds-cadastro-prd"
  engine                      = "mysql"
  engine_version              = "8.0"
  instance_class              = "db.t3.medium"
  allocated_storage           = 50
  db_name                     = "cadastro"
  username                    = "app_admin"
  manage_master_user_password = true
  db_subnet_group_name        = "subnets-publicas"
  vpc_security_group_ids      = ["sg-0ee55ff66aa77bb88"]
  publicly_accessible         = true
  storage_encrypted           = true
  backup_retention_period     = 7
  deletion_protection         = true
  skip_final_snapshot         = false

  tags = {
    Ambiente = "producao"
  }
}
