# Análise de segurança – Terraform AWS

## 1. Escopo e abordagem

**Escopo:** os 4 arquivos de `terraform/aws/` (`s3.tf`, `security-group.tf`, `ebs.tf`, `rds.tf`), com 14 recursos no total.
A análise é **estática**: não roda `terraform plan` nem `apply` e não acessa a AWS.

Fiz a análise em **3 etapas**:

**Etapa 1 – Entender as ferramentas.** Revisei o que é o Terraform, como a linguagem HCL descreve recursos de nuvem (`resource "tipo" "nome" { atributos }`) e quais opções existem para analisar esses arquivos sem acessar a nuvem (python-hcl2, Checkov, OPA, c7n-left).

**Etapa 2 – Ler cada arquivo, recurso por recurso.** Li todos os recursos, atributo por atributo, e apliquei a cada um 5 perguntas:

1. **O que é?** Qual o papel do recurso e que dado ele guarda ou transporta.
2. **Quem alcança?** Internet, rede interna ou apenas outros recursos.
3. **Os dados estão protegidos?** Criptografia em repouso e em trânsito, e quem controla a chave.
4. **Sobrevive a erro ou ataque?** Backup, versionamento, proteção contra exclusão.
5. **Como é o acesso?** Autenticação, credenciais e privilégio mínimo.

**Etapa 3 – Mapear o risco.** Consolidei os achados (seção 2), classifiquei a severidade de cada um (critério na seção 6) e escolhi os 2 mais críticos para automatizar. Por fim, comparei o resultado com o Checkov (seção 5).

O uso de IA ao longo dessas etapas está registrado em [uso-de-ia.md](uso-de-ia.md).

## 2. Achados

| Recurso | Arquivo | Status | Problema | Risco | Recomendação | Severidade |
|---|---|---|---|---|---|---|
| `aws_s3_bucket.exportacao_clientes` (+ `public_access_block` e `bucket_policy`) | `s3.tf` | ❌ | As 4 travas do bloqueio de acesso público estão em `false`, e a bucket policy concede `s3:GetObject` e `s3:ListBucket` a `Principal "*"` | Qualquer pessoa na internet lista e baixa os arquivos de exportação de clientes, **sem autenticação** e sem depender de nenhuma outra falha (vazamento de dados pessoais, LGPD) | Definir as 4 travas como `true`; remover o `Principal "*"` da policy; para compartilhamento externo, usar URLs pré-assinadas com validade curta | **Crítica** |
| `aws_security_group.app` | `security-group.tf` | ❌ | Entrada na porta 22 (SSH) a partir de `0.0.0.0/0` | Os servidores de aplicação ficam expostos a varredura e força bruta de SSH vindas de toda a internet; uma credencial fraca ou uma vulnerabilidade no SSH dá acesso ao backend | Remover a regra; usar AWS SSM Session Manager ou restringir a origem à rede corporativa/VPN (como já é feito no `monitoramento`) | **Alta** |
| `aws_db_instance.cadastro` | `rds.tf` | ❌ | `publicly_accessible = true` em `db_subnet_group_name = "subnets-publicas"` | O banco de cadastro (dados pessoais) recebe IP público e fica a uma única camada (o Security Group, que não está nos arquivos) da internet | `publicly_accessible = false`, subnets privadas, acesso administrativo via VPN/bastion/SSM | **Alta** |
| `aws_ebs_volume.logs_processamento` | `ebs.tf` | ❌ | `encrypted = false` | Snapshots e cópias do volume ficam legíveis por quem obtiver acesso a eles (snapshot compartilhado por engano, conta comprometida). Logs costumam conter dados sensíveis | `encrypted = true` com `kms_key_id` (CMK); ativar a criptografia por padrão do EBS na conta | **Média** |
| `aws_security_group.web` e `.app` | `security-group.tf` | ⚠️ | Saída liberada para qualquer destino (`protocol = "-1"`, `0.0.0.0/0`) | Facilita a exfiltração de dados e a comunicação com servidores de comando e controle se um servidor for comprometido | Restringir a saída aos destinos e portas necessários | Baixa |
| `aws_db_instance.cadastro` e `.pagamentos` | `rds.tf` | ⚠️ | `storage_encrypted = true` sem `kms_key_id` | Usa a chave gerenciada pela AWS (`aws/rds`): não dá para restringir quem usa a chave nem compartilhar snapshots criptografados com outras contas | Usar CMK própria por sistema | Baixa |
| `aws_db_instance.cadastro` e `.pagamentos` | `rds.tf` | ⚠️ | `username = "app_admin"` é o usuário master, e o nome sugere uso pela aplicação | Se a aplicação usa o master, uma injeção de SQL ganha privilégio total no banco | Criar um usuário de aplicação com privilégio mínimo; reservar o master para administração | Baixa |
| `aws_s3_bucket.relatorios_financeiros` e `aws_ebs_volume.dados_aplicacao` | `s3.tf`, `ebs.tf` | ⚠️ | A mesma CMK (`key/1a2b3c4d-...`) protege o S3 financeiro e o volume da aplicação | Quem tem permissão na chave por causa de um sistema também decifra o outro; o raio de impacto aumenta | Uma CMK por sistema ou classe de dado | Baixa |
| `aws_s3_bucket.exportacao_clientes` | `s3.tf` | ⚠️ | Sem versionamento e sem criptografia com KMS própria (fica só a SSE-S3 padrão da AWS) | Exclusão ou sobrescrita (acidental ou ransomware) sem recuperação; sem controle de acesso pela chave | `aws_s3_bucket_versioning` e SSE-KMS com CMK | Baixa |
| `aws_s3_bucket.relatorios_financeiros` | `s3.tf` | ⚠️ | Sem logs de acesso e sem policy que force HTTPS (`aws:SecureTransport`) | Sem trilha de quem acessou os relatórios; a requisição pode ser feita sem TLS | Ativar server access logging (ou eventos de dados no CloudTrail) e negar `aws:SecureTransport = false` | Baixa |
| `aws_s3_bucket.relatorios_financeiros` | `s3.tf` | ✅ | — | Bloqueio público completo, SSE-KMS com CMK e versionamento | — | — |
| `aws_security_group.web` (entrada) | `security-group.tf` | ✅ | — | Só a porta 443 é aberta à internet, o esperado para um load balancer público | — | — |
| `aws_security_group.monitoramento` | `security-group.tf` | ✅ | — | SSH só da rede corporativa (`10.20.0.0/16`); saída restrita a 443 na rede interna | — | — |
| `aws_ebs_volume.dados_aplicacao` | `ebs.tf` | ✅ | — | Criptografado com CMK | — | — |
| `aws_db_instance.pagamentos` | `rds.tf` | ✅ | — | Não público, subnets privadas, criptografado, backup de 7 dias, proteção contra exclusão, senha gerenciada pelo Secrets Manager | — | — |

Os 2 achados automatizados como controles são o **S3 `exportacao_clientes` (CTRL-AWS-001)** e o **RDS `cadastro` (CTRL-AWS-002)**: os dois cenários que expõem **diretamente** dados de clientes.

## 3. Observação de projeto (não é vulnerabilidade)

- **`rds.tf` fora do padrão do `terraform fmt`:** detectado pelo `terraform fmt -check` (exit code 3). Na cópia, corrigi só o alinhamento dos `=`, sem mudar nenhum valor.

## 4. Itens não avaliáveis (fora dos arquivos)

- **Security Groups dos bancos** (`sg-0aa11...`, `sg-0ee55...`): só os IDs aparecem. A exposição real do `cadastro` depende deles.
- **Subnets:** `subnets-publicas` e `subnets-privadas-dados` são apenas nomes; não dá para confirmar se a subnet tem de fato saída para a internet.
- **Permissões IAM e key policies das chaves KMS:** quem pode ler os buckets, usar as chaves e restaurar snapshots.

## 5. Comparação com o Checkov

Executei `checkov -d terraform/aws --framework terraform` (Checkov 3.4.6): **48 checks aprovados e 42 com falha**, em 14 recursos.

**O Checkov também encontrou (concordo):**

| Achado | Check do Checkov |
|---|---|
| S3 `exportacao_clientes` com bloqueio público desligado | `CKV_AWS_53`, `54`, `55`, `56` (no bloqueio) e `CKV2_AWS_6` (no bucket) |
| RDS `cadastro` público | `CKV_AWS_17` |
| SSH aberto no SG `app` | `CKV_AWS_24` |
| EBS `logs_processamento` sem criptografia | `CKV_AWS_3` (e `CKV_AWS_189`: sem CMK) |
| Saída liberada em `web` e `app` | `CKV_AWS_382` |
| `exportacao_clientes` sem versionamento nem KMS; buckets sem logs de acesso | `CKV_AWS_21`, `CKV_AWS_145`, `CKV_AWS_18` |

O veredito do Checkov foi **igual** ao dos meus controles: FAIL em `exportacao_clientes` e `cadastro`, PASS em `relatorios_financeiros` e `pagamentos`.

**O Checkov apontou a mais (concordo em parte):**

- **Resiliência e operação**, por exemplo Multi-AZ (`CKV_AWS_157`), replicação entre regiões (`CKV_AWS_144`), lifecycle (`CKV2_AWS_61`), atualização automática de versão menor (`CKV_AWS_226`) e cópia de tags para snapshots (`CKV2_AWS_60`). São boas práticas, mas dependem de requisitos de negócio (custo, RTO/RPO). Não as classifico como falha de segurança.
- **Observabilidade e acesso**, por exemplo logs do RDS (`CKV_AWS_129`, `CKV2_AWS_30`), enhanced monitoring (`CKV_AWS_118`), performance insights (`CKV_AWS_353`), autenticação IAM no RDS (`CKV_AWS_161`) e notificações de eventos no S3 (`CKV2_AWS_62`). Concordo como melhoria de severidade Baixa; os logs ajudam a detectar e investigar incidentes.
- **`CKV_AWS_23` (descrição em SGs e regras):** está tecnicamente correto (as regras de saída não têm descrição), mas o impacto é só de documentação.

**Discordo:**

- **`CKV2_AWS_5` (Security Group não anexado a nenhum recurso):** é um falso positivo causado pelo recorte do material. As instâncias e o load balancer que usariam os SGs não estão nos arquivos.

**Encontrei e o Checkov não apontou:**

- A **bucket policy com `Principal "*"`** no `exportacao_clientes`. Nenhum check falhou no recurso `aws_s3_bucket_policy`; o Checkov só pegou o problema indiretamente, pelas travas do bloqueio.
- Possível uso do **usuário master** pela aplicação, **CMK compartilhada** entre sistemas, **policy sem HTTPS obrigatório** no `relatorios_financeiros`.
- A formatação fora do padrão no `rds.tf` (seção 3).

**Conclusão:** o Checkov é ótimo para cobertura ampla e funcionou como "gabarito" para validar a minha análise. Mas ele mistura severidades e gera ruído. Por isso, no pipeline, ele é **informativo**, e o **gate** são os 2 controles, com regra, severidade e mensagem que eu consigo explicar.

## 6. Critério de severidade

| Severidade | Critério | Exemplo nesta análise |
|---|---|---|
| **Crítica** | Dado sensível exposto **sem depender de nenhuma outra falha** | Bucket legível por qualquer pessoa na internet |
| **Alta** | Serviço sensível exposto diretamente à internet; falta **uma** falha para o comprometimento | SSH aberto ao mundo; banco com IP público |
| **Média** | Só é explorável **depois** de outra falha | Volume sem criptografia (exige acesso ao snapshot) |
| **Baixa** | Melhoria de defesa em profundidade, rastreabilidade ou privilégio mínimo | Saída liberada, KMS padrão, falta de logs |
