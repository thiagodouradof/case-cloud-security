# Desafio Técnico – Cloud Security (AWS)

## 1. Objetivo

Analisar 4 arquivos Terraform da AWS, automatizar **2 controles de segurança** com resultado PASS/FAIL e integrá-los a um pipeline de CI/CD que **bloqueia o deploy** quando há falha.
Tudo é **estático e local**: nenhum `terraform plan`/`apply`, nenhum acesso à AWS, nenhuma credencial.

## 2. Abordagem

1. **Entender as ferramentas:** Terraform/HCL e as opções de análise estática (python-hcl2, Checkov, OPA/Rego, c7n-left).
2. **Ler cada arquivo a fundo**, recurso por recurso, atributo por atributo, com 5 perguntas:
   *O que é? Quem alcança? Os dados estão protegidos? Sobrevive a erro ou ataque? Como é o acesso?*
3. **Consolidar os achados**, classificar por severidade e automatizar os 2 mais críticos → [analise.md](analise.md).

## 3. Pré-requisitos e instalação

- Python 3.10+ (testado com 3.14)
- Opcionais: Terraform (validação de sintaxe) e Checkov (comparação)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # python-hcl2 e pytest, com versão fixa
```

O Checkov fica **fora** do `requirements.txt`, porque é uma ferramenta à parte e tem muitas dependências:
`pip install checkov==3.4.6` (de preferência num venv separado).

## 4. Como executar

```bash
python -m src.main terraform/aws          # validação de segurança (aceita pasta ou arquivo .tf)
python -m src.main terraform/cenarios/remediado   # mesmo código, com as remediações aplicadas: tudo PASS, exit 0
pytest -v                                 # testes dos controles
checkov -d terraform/aws --framework terraform --soft-fail   # comparação com ferramenta de mercado

cd terraform/aws                          # sintaxe Terraform (não acessa a AWS)
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

## 5. Exemplo de saída e exit code

```
Validação de segurança – terraform/aws

PASS [CTRL-AWS-001][CRITICA] aws_s3_bucket.relatorios_financeiros: bloqueio de acesso público completo.
FAIL [CTRL-AWS-001][CRITICA] aws_s3_bucket.exportacao_clientes: bloqueio de acesso público incompleto. Travas desligadas: block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets. Risco: o bucket pode ser exposto à internet (ex.: policy com Principal "*"). Remediação: definir as 4 travas como true; para compartilhamento externo, usar URLs pré-assinadas.
PASS [CTRL-AWS-002][ALTA] aws_db_instance.pagamentos: banco não é publicamente acessível.
FAIL [CTRL-AWS-002][ALTA] aws_db_instance.cadastro: banco publicamente acessível (publicly_accessible = true). O banco recebe IP público e fica a uma única camada (Security Group) da internet. Remediação: definir publicly_accessible = false e usar subnets privadas; acesso administrativo via VPN/bastion/SSM.

Resumo: 4 verificações | 2 PASS | 2 FAIL
Resultado: FAIL – deploy bloqueado.
```

| Exit code | Significado | No pipeline |
|---|---|---|
| `0` | Nenhum FAIL | Job verde, deploy liberado |
| `1` | Ao menos um FAIL | Job vermelho, **deploy bloqueado** |
| `2` | Erro de leitura (arquivo inexistente, HCL inválido) ou de uso | Job vermelho: na dúvida, não libera |

O pipeline não lê o texto da saída: ele decide pelo **exit code**, que é o contrato padrão entre um programa e o CI.

## 6. Controles implementados

| ID | O que verifica | Severidade | Por que foi escolhido | Equivalente no Checkov |
|---|---|---|---|---|
| **CTRL-AWS-001** | Cada `aws_s3_bucket` precisa de um `aws_s3_bucket_public_access_block` (ligado por referência ou pelo nome literal) com as 4 travas em `true`. Trava ausente conta como desligada | **CRÍTICA** | `exportacao_clientes` expõe dados de clientes a qualquer pessoa, sem autenticação | `CKV_AWS_53`, `54`, `55`, `56` (uma por trava) e `CKV2_AWS_6` (correlação bucket ↔ bloqueio) |
| **CTRL-AWS-002** | `aws_db_instance` com `publicly_accessible = true` → FAIL. Ausente → PASS (o padrão do provider AWS é `false`). Valor não verificável estaticamente (ex.: `var.x`) → FAIL | **ALTA** | `cadastro` guarda dados pessoais (LGPD) e tem IP público em subnet pública | `CKV_AWS_17` |

Os IDs do Checkov foram **confirmados executando o Checkov 3.4.6**: o veredito dele é igual ao dos dois controles em todos os recursos.

**Por que não os outros achados?** O SSH aberto (Alta) e o EBS sem criptografia (Média) ficam como próximos controles: priorizei os dois cenários que **expõem diretamente dados de clientes**.

### Estrutura do código

```
src/leitor_tf.py                     lê .tf com python-hcl2 e limpa o formato (aspas, ${ }, "true")
src/controles/s3_acesso_publico.py   CTRL-AWS-001
src/controles/rds_acesso_publico.py  CTRL-AWS-002
src/main.py                          roda a lista CONTROLES, imprime e define o exit code
tests/                               exemplos .tf conformes/não conformes + testes unitários e de integração
```

Cada controle é **uma função** que recebe o **dicionário de configuração** e devolve uma lista de resultados (`controle`, `recurso`, `status`, `severidade`, `mensagem`). Assim, a leitura fica separada da regra: os testes passam dicionários prontos, e a forma de leitura pode mudar (ex.: JSON de `terraform show -json`) sem alterar os controles.
Para **adicionar um 3º controle**, basta criar a função em `src/controles/` e incluí-la na lista `CONTROLES` do `main.py`.

## 7. Decisões técnicas e alternativas consideradas

| Alternativa | Por que não como principal |
|---|---|
| **Checkov puro** | Cobertura ampla, mas 42 falhas de severidades misturadas, muitas de resiliência/operação. Como gate, bloquearia o deploy por itens de baixo risco. Uso como **gabarito** e como etapa **informativa** no pipeline. |
| **OPA / Rego** | Padrão de mercado para *policy as code*, mas exige aprender uma linguagem nova e, normalmente, rodar sobre o JSON do `terraform plan`, que é proibido neste desafio. |
| **c7n-left (Cloud Custodian)** | Interessante porque usa a mesma linguagem no pipeline e na conta real (ver [evolucao.md](evolucao.md)), mas acrescenta uma dependência grande para 2 controles. |
| **Python + python-hcl2** (escolhido) | Lógica transparente e explicável linha a linha, fácil de alterar, mensagens em português e só 2 dependências. |

## 8. Pipeline

[pipeline/security.yml](pipeline/security.yml): um workflow do GitHub Actions, disparado em `push` e `pull_request`.

> O arquivo fica em `pipeline/`, como pedem os entregáveis do desafio. Para o GitHub executá-lo de verdade, basta copiá-lo para `.github/workflows/`, que é a pasta lida pelo GitHub Actions. As mesmas etapas podem ser rodadas localmente, uma a uma (ver seção 4).

```
commit ─► sintaxe ─┬─► seguranca (GATE) ─► deploy (conceitual, só na main)
                   └─► checkov (informativo, --soft-fail)
```

| Job | O que faz |
|---|---|
| `sintaxe` | `terraform fmt -check`, `init -backend=false`, `validate`. Barato e rápido, por isso vem primeiro |
| `seguranca` | `pytest` (garante que os controles funcionam) e depois `python -m src.main terraform/aws`. **O exit code 1 deixa o job vermelho** |
| `checkov` | Cobertura ampla, **não bloqueia**: o gate são os meus controles |
| `deploy` | Só `echo`. Nenhuma credencial, nenhum `plan`/`apply`. Depende do `seguranca` |

> **O pipeline fica vermelho por design.** Os `.tf` do desafio têm problemas reais, então o job `seguranca` falha e o `deploy` é **pulado**. Com as remediações aplicadas (`terraform/cenarios/remediado`), a validação devolve exit 0 e o deploy seria liberado. Isso prova que o gate funciona: é exatamente aí que um deploy inseguro seria barrado.

O workflow usa `permissions: contents: read` (menor privilégio) e foi verificado com o próprio Checkov (`--framework github_actions`): 80 checks aprovados, 0 falhas.

## 9. Limitações e próximos passos

**Limitações dos controles atuais:**
- CTRL-AWS-001 não analisa o conteúdo da `aws_s3_bucket_policy` (o `jsonencode()` chega como texto não resolvido) nem o bloqueio no nível da conta (`aws_s3_account_public_access_block`).
- CTRL-AWS-002 não avalia `aws_rds_cluster_instance` (Aurora), não confirma se a subnet é de fato pública (só temos o nome) e não avalia o Security Group do banco, que não está nos arquivos.
- A análise é estática: variáveis, módulos e valores calculados não são resolvidos (no RDS, um valor não verificável resulta em FAIL por precaução).
- Um arquivo sem S3 nem RDS resulta em "0 verificações" e PASS: nada no escopo dos 2 controles.
- O leitor limpa o `${ }` de referências simples; textos com várias interpolações (`"${a}-${b}"`) não são tratados.

**Próximos passos:**
- Novos controles: SSH aberto ao mundo (`aws_security_group`) e EBS sem criptografia (`aws_ebs_volume`).
- Cobrir `aws_rds_cluster_instance` e a policy com `Principal "*"`.
- Saída em JSON/SARIF para exibir os achados direto no GitHub.
- Processo de exceção (risco aceito com dono e prazo).
- Escalar para várias contas → [evolucao.md](evolucao.md).

## 10. Documentos

- [analise.md](analise.md): análise completa dos 14 recursos, severidades e comparação com o Checkov
- [evolucao.md](evolucao.md): evolução para um ambiente com múltiplas contas AWS (e paralelo com o Azure)
- [uso-de-ia.md](uso-de-ia.md): como a IA foi usada neste desafio
