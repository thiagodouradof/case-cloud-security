resource "aws_security_group" "web" {
  name        = "web-publico"
  description = "Load balancer da aplicacao web"
  vpc_id      = "vpc-0a1b2c3d4e5f60718"

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Ambiente = "producao"
  }
}

resource "aws_security_group" "app" {
  name        = "app-backend"
  description = "Servidores de aplicacao"
  vpc_id      = "vpc-0a1b2c3d4e5f60718"

  ingress {
    description     = "Trafego vindo do load balancer"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Ambiente = "producao"
  }
}

resource "aws_security_group" "monitoramento" {
  name        = "monitoramento"
  description = "Agentes de monitoramento"
  vpc_id      = "vpc-0a1b2c3d4e5f60718"

  ingress {
    description = "SSH a partir da rede corporativa"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.20.0.0/16"]
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  tags = {
    Ambiente = "producao"
  }
}
