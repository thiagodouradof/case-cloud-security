# Uso de IA neste desafio

> Esqueleto: as respostas são preenchidas por mim. Os comentários `<!-- -->` são lembretes e podem ser apagados.

## 1. Quais ferramentas de IA utilizei?

<!-- Ex.: Claude (chat) para estudo e definição da arquitetura; Claude Code para implementação. -->

## 2. Em quais partes a IA ajudou?

<!-- Estudo (Terraform/HCL, Checkov, OPA, c7n-left), estrutura do repositório, código, testes, pipeline, documentação. -->

## 3. O que eu revisei ou modifiquei?

<!-- O que conferi linha a linha, o que reescrevi à mão, o que mudei de nome/mensagem/regra. -->

## 4. Uma sugestão da IA que foi corrigida, descartada ou adaptada

<!--
Candidatos reais desta jornada (escolher um ou mais e contar com as minhas palavras):
- A IA sugeriu o Security Group (SSH) como 2º controle; escolhi o RDS por expor diretamente dados pessoais.
- Afirmações da IA foram verificadas executando as ferramentas:
  - falha do `terraform fmt` no `rds.tf` (confirmada: exit code 3);
  - IDs do Checkov (confirmados com o Checkov 3.4.6; além disso apareceu o CKV2_AWS_6, que não estava previsto);
  - formato do `python-hcl2` (inspecionado antes de escrever o leitor: lista de blocos e aspas mantidas no tipo e no nome);
  - nomes das regras do AWS Config (confirmados na documentação da AWS).
- Problemas que só apareceram na execução: arquivo .tf com BOM quebrando o parser; limite de 260 caracteres de caminho no Windows ao criar o venv.
- Sugestão adaptada: o CTRL-AWS-002 reprova valores não verificáveis (ex.: var.publico), em vez de aprovar sem perceber.
-->

## 5. O que aprendi?

<!-- Técnico (HCL, controles, pipeline, multi-conta) e sobre o próprio uso de IA (verificar antes de confiar). -->
