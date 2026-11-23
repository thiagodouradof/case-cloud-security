# Material do desafio - AWS

Este diretório contém configurações fictícias de infraestrutura utilizadas exclusivamente para o desafio técnico.

Analise os arquivos e identifique configurações que você considere adequadas ou inadequadas sob a perspectiva de Cloud Security.

Não execute terraform plan nem terraform apply.

Nenhum recurso deverá ser provisionado.

Você deverá selecionar dois dos problemas encontrados e desenvolver as validações solicitadas no desafio.

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `s3.tf` | Buckets Amazon S3 |
| `security-group.tf` | Security Groups |
| `ebs.tf` | Volumes Amazon EBS |
| `rds.tf` | Instâncias Amazon RDS |

## Execução local (opcional)

Os arquivos não dependem de conta AWS nem de credenciais. Caso deseje verificar a sintaxe localmente:

```bash
terraform init -backend=false
terraform fmt -check
terraform validate
```
