resource "aws_ebs_volume" "dados_aplicacao" {
  availability_zone = "sa-east-1a"
  size              = 100
  type              = "gp3"
  encrypted         = true
  kms_key_id        = "arn:aws:kms:sa-east-1:111122223333:key/1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"

  tags = {
    Name     = "ebs-dados-aplicacao"
    Ambiente = "producao"
  }
}

resource "aws_ebs_volume" "logs_processamento" {
  availability_zone = "sa-east-1a"
  size              = 200
  type              = "gp3"
  encrypted         = false

  tags = {
    Name     = "ebs-logs-processamento"
    Ambiente = "producao"
  }
}
