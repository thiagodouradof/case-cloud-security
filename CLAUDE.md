# Desafio Técnico – Cloud Security (AWS) · Especificação para o Claude Code

> Este arquivo fica na raiz do repositório. Ele descreve **o que construir, como e em que ordem**.
> As decisões abaixo **já foram tomadas e justificadas**. Não as altere sem perguntar.

---

## 0. Contexto

Desafio de processo seletivo (Engenharia de Segurança da Informação Júnior – Cloud Security).
Recebi 4 arquivos Terraform de AWS (`s3.tf`, `security-group.tf`, `ebs.tf`, `rds.tf`), com configurações seguras e inseguras. Preciso:

1. Analisar os arquivos (status, problema, risco, remediação).
2. Automatizar **2 controles** com PASS/FAIL e mensagens claras.
3. Demonstrar a integração com CI/CD (Commit → sintaxe → segurança → PASS/FAIL → deploy conceitual).
4. Explicar a evolução para um ambiente com múltiplas contas AWS.

**Premissas obrigatórias do desafio:**
- Tudo **estático e local**. Nunca executar `terraform plan` ou `terraform apply`.
- Não acessar AWS. Não usar credenciais, tokens, segredos ou dados reais.
- Evitar dependências e complexidade desnecessárias.

---

## 1. Como você (Claude Code) deve trabalhar

Eu sou desenvolvedor web em transição para segurança. **Vou reescrever todo o código à mão** no ambiente da minha empresa e **defendê-lo ao vivo** em entrevista, onde pedirão uma pequena alteração. Portanto:

- **Código simples e legível > código sofisticado.** Funções pequenas, `if`/`for` explícitos, dicionários e listas. Sem classes, herança, decorators, metaprogramação ou frameworks.
- **Nomes e comentários em português**, coerentes com o enunciado.
- **Arquivos curtos.** Meta: o código de `src/` inteiro com **menos de ~200 linhas**.
- **Dependências:** apenas `python-hcl2` e `pytest` (Python 3.10+). O Checkov é ferramenta à parte, fora do `requirements.txt`.
- **Trabalhe por fases** (seção 6). Ao final de cada fase: **pare, explique o que fez arquivo por arquivo e aguarde meu OK.**
- Depois de criar cada arquivo de código, explique em linguagem simples o que cada função faz e por quê.
- Se algo do enunciado for ambíguo, **pergunte** em vez de assumir.
- Nunca invente IDs, nomes de regras ou comportamentos de ferramentas. Se não tiver certeza, marque como `A CONFIRMAR`.

---

## 2. Decisões já tomadas

| Decisão | Escolha | Justificativa |
|---|---|---|
| Provedor | **AWS** | Tenho mais familiaridade; o enunciado exige um único provedor. Azure aparece só como parecer no `evolucao.md` |
| Abordagem dos controles | **Python + `python-hcl2`** | Lógica transparente e explicável linha a linha; fácil de alterar ao vivo; mensagens em português |
| Ferramenta de mercado | **Checkov** | Usado para validar a minha análise (gabarito) e no pipeline como cobertura ampla complementar |
| Controle 1 | **CTRL-AWS-001 – S3 sem bloqueio de acesso público** | Severidade **Crítica**: `exportacao_clientes` expõe dados de clientes a qualquer pessoa, sem autenticação |
| Controle 2 | **CTRL-AWS-002 – RDS publicamente acessível** | Severidade **Alta**: `cadastro` (dados pessoais/LGPD) com IP público em subnet pública |
| Por que não o Security Group com SSH aberto | Fica como próximo controle | Também é Alto, mas priorizei os dois cenários que **expõem diretamente dados de clientes** |
| Por que não o EBS sem criptografia | Fica como próximo controle | Severidade Média: depende de outra falha (acesso a snapshot) para ser explorado |

**Minha abordagem (usar no README e na apresentação):**
1. Entender as ferramentas: Terraform/HCL, opções de análise estática (python-hcl2, Checkov, OPA, c7n-left).
2. Ler cada arquivo a fundo, recurso por recurso, atributo por atributo, aplicando 5 perguntas:
   *O que é? Quem alcança? Os dados estão protegidos? Sobrevive a erro ou ataque? Como é o acesso?*
3. Consolidar os achados, classificar por severidade e automatizar os 2 mais críticos.

---

## 3. Estrutura do repositório

```
desafio-cloud-security/
├── CLAUDE.md                      ← este arquivo
├── README.md
├── analise.md
├── evolucao.md
├── uso-de-ia.md
├── requirements.txt               ← python-hcl2, pytest
├── .gitignore                     ← .venv/, .terraform/, __pycache__/, .pytest_cache/
├── .github/
│   └── workflows/
│       └── security.yml           ← pipeline (executa de verdade no GitHub Actions)
├── terraform/
│   └── aws/                       ← cópia dos 4 .tf originais + README.md do material
├── src/
│   ├── __init__.py
│   ├── leitor_tf.py               ← lê .tf e devolve dicionário
│   ├── controles/
│   │   ├── __init__.py
│   │   ├── s3_acesso_publico.py   ← CTRL-AWS-001
│   │   └── rds_acesso_publico.py  ← CTRL-AWS-002
│   └── main.py                    ← roda os controles, imprime, define exit code
└── tests/
    ├── exemplos/                  ← .tf pequenos: conformes e não conformes
    ├── test_s3.py
    ├── test_rds.py
    └── test_integracao.py
```

---

## 4. Especificação dos componentes

### 4.1 Formato padrão de resultado (todos os controles devolvem isto)

Cada controle é **uma função** que recebe o **dicionário de configuração** (já lido) e devolve uma **lista de resultados**:

```python
{
    "controle": "CTRL-AWS-002",
    "recurso": "aws_db_instance.cadastro",   # endereço Terraform: tipo.nome
    "status": "FAIL",                         # "PASS" ou "FAIL"
    "severidade": "ALTA",
    "mensagem": "Banco publicamente acessível (publicly_accessible = true). ..."
}
```

**Por que o controle recebe um dicionário e não um caminho de arquivo:** desacopla a leitura da regra. Os testes podem passar um dicionário pronto (como no exemplo do enunciado `{ "resource": "audit-log", "enabled": false }`), e a forma de leitura pode mudar no futuro (por exemplo, JSON de `terraform show -json`) sem alterar os controles.

### 4.2 `src/leitor_tf.py`

**Primeiro passo obrigatório:** antes de escrever qualquer controle, rode o `python-hcl2` sobre `terraform/aws/s3.tf` e `rds.tf` e **me mostre o dicionário resultante** (`json.dumps(..., indent=2)`). O formato varia entre versões da biblioteca (blocos como listas, referências `${...}`, aspas em strings). O código deve se basear no formato **observado**, não suposto.

Funções esperadas:
- `carregar_arquivo(caminho) -> dict`: lê um `.tf`.
- `carregar_pasta(caminho) -> dict`: lê todos os `.tf` de uma pasta e **junta os `resource`** num único dicionário (o Terraform trata a pasta inteira como um só projeto).
- `listar_recursos(config, tipo) -> list[tuple[str, dict]]`: devolve `[(nome, atributos), ...]` para um tipo, por exemplo `aws_db_instance`.
- Pequenos auxiliares de normalização, **se o formato observado exigir**: por exemplo, interpretar `true`/`"true"` como booleano e remover `${ }` de referências.

Tratar erro de leitura (arquivo inexistente ou HCL inválido) com mensagem clara, sem stack trace para o usuário.

### 4.3 CTRL-AWS-002: RDS publicamente acessível (implementar primeiro, é o mais simples)

- **Recursos avaliados:** `aws_db_instance`.
- **Regra:**
  - `publicly_accessible = true` → **FAIL**
  - `publicly_accessible = false` → **PASS**
  - atributo ausente → **PASS** (o padrão do provider é `false`; citar no README)
  - qualquer outro valor (ex.: `var.publico`, não resolvível sem `plan`) → **FAIL** por precaução (aprovado na fase 3)
- **Mensagem de FAIL** (problema + risco + remediação):
  `FAIL [CTRL-AWS-002][ALTA] aws_db_instance.cadastro: banco publicamente acessível (publicly_accessible = true). O banco recebe IP público e fica a uma única camada (Security Group) da internet. Remediação: definir publicly_accessible = false e usar subnets privadas; acesso administrativo via VPN/bastion/SSM.`
- **Equivalente no Checkov:** `CKV_AWS_17` ("Ensure all data stored in RDS is not publicly accessible"). **Confirmado** com Checkov 3.4.6: FAIL em `cadastro`, PASS em `pagamentos`, o mesmo veredito do CTRL-AWS-002.
- **Limitações a documentar:** não avalia `aws_rds_cluster_instance` (Aurora); não verifica se a subnet é de fato pública (só temos o nome); não avalia o Security Group do banco, que não está nos arquivos.
- *Opcional, se sobrar tempo:* aplicar a mesma regra a `aws_rds_cluster_instance`.

### 4.4 CTRL-AWS-001: S3 sem bloqueio de acesso público

- **Recursos avaliados:** cada `aws_s3_bucket`, correlacionado com o `aws_s3_bucket_public_access_block` que aponta para ele.
- **Correlação:** um bloqueio pertence ao bucket `N` quando o atributo `bucket` do bloqueio:
  - referencia `aws_s3_bucket.N` (ex.: `aws_s3_bucket.N.id` ou `aws_s3_bucket.N.bucket`), **ou**
  - é igual ao nome literal do bucket (atributo `bucket` do `aws_s3_bucket`).
- **Regra:**
  - Bucket **sem** bloqueio associado → **FAIL** ("nenhum bloqueio de acesso público declarado").
  - Bloqueio com **qualquer** das 4 travas diferente de `true` → **FAIL**, listando quais estão abertas:
    `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`.
  - Trava **ausente** conta como aberta (o padrão do recurso é `false`).
  - As 4 em `true` → **PASS**.
- **Mensagem de FAIL (exemplo):**
  `FAIL [CTRL-AWS-001][CRITICA] aws_s3_bucket.exportacao_clientes: bloqueio de acesso público incompleto. Travas desligadas: block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets. Risco: o bucket pode ser exposto à internet (ex.: policy com Principal "*"). Remediação: definir as 4 travas como true; para compartilhamento externo, usar URLs pré-assinadas.`
- **Equivalente no Checkov:** **confirmado** com Checkov 3.4.6, com o mesmo veredito do CTRL-AWS-001 (FAIL em `exportacao_clientes`, PASS em `relatorios_financeiros`):
  - `CKV_AWS_53` (block_public_acls), `CKV_AWS_54` (block_public_policy), `CKV_AWS_55` (ignore_public_acls), `CKV_AWS_56` (restrict_public_buckets): uma verificação por trava, reportada no recurso `aws_s3_bucket_public_access_block`;
  - `CKV2_AWS_6` ("Ensure that S3 bucket has a Public Access block"): verificação de grafo reportada no recurso `aws_s3_bucket`, que correlaciona bucket e bloqueio, como o nosso controle.
- **Fora do escopo da v1 (documentar como limitação/evolução):** analisar o conteúdo da `aws_s3_bucket_policy` (`Principal "*"`), porque o `jsonencode()` chega como texto não resolvido; bloqueio no nível da conta (`aws_s3_account_public_access_block`).

### 4.5 `src/main.py` (runner)

- Uso: `python -m src.main terraform/aws` (aceitar pasta **ou** um arquivo `.tf`).
- Executa os 2 controles e imprime **uma linha por resultado** + um resumo:

```
Validação de segurança – terraform/aws

PASS [CTRL-AWS-001][CRITICA] aws_s3_bucket.relatorios_financeiros: bloqueio de acesso público completo.
FAIL [CTRL-AWS-001][CRITICA] aws_s3_bucket.exportacao_clientes: ...
PASS [CTRL-AWS-002][ALTA] aws_db_instance.pagamentos: banco não é publicamente acessível.
FAIL [CTRL-AWS-002][ALTA] aws_db_instance.cadastro: ...

Resumo: 4 verificações | 2 PASS | 2 FAIL
Resultado: FAIL – deploy bloqueado.
```

- **Exit code:** `0` se não houver FAIL; `1` se houver ao menos um FAIL; `2` em erro de leitura. É o exit code que o pipeline usa para bloquear o deploy. Explicar isso no README.
- A lista de controles fica numa lista Python simples no topo do arquivo, para que **adicionar um 3º controle** seja importar e incluir uma função (provável pedido na entrevista).

### 4.6 Testes (`tests/`)

Arquivos em `tests/exemplos/` (pequenos, só com o necessário):

| Arquivo | Cenário | Esperado |
|---|---|---|
| `rds_conforme.tf` | `publicly_accessible = false` | PASS |
| `rds_sem_atributo.tf` | atributo ausente | PASS |
| `rds_nao_conforme.tf` | `publicly_accessible = true` | FAIL |
| `s3_conforme.tf` | bucket + 4 travas `true` | PASS |
| `s3_nao_conforme.tf` | bucket + 4 travas `false` | FAIL (lista as 4) |
| `s3_trava_parcial.tf` | 3 travas `true`, 1 `false` | FAIL (lista só a aberta) |
| `s3_sem_bloqueio.tf` | bucket sem `public_access_block` | FAIL |

Testes:
- `test_rds.py` / `test_s3.py`: um teste por linha da tabela, mais pelo menos um teste usando **dicionário direto** (sem arquivo), demonstrando o formato "objeto de configuração" do enunciado.
- `test_integracao.py`: rodar sobre `terraform/aws/` e verificar que **só** `exportacao_clientes` e `cadastro` falham, e que o exit code é `1`.
- Rodar com `pytest -v`.

### 4.7 Pipeline: `.github/workflows/security.yml`

Gatilhos: `push` e `pull_request`. Jobs em sequência (`needs`):

1. **`sintaxe`**: `terraform fmt -check -recursive`, `terraform init -backend=false`, `terraform validate` em `terraform/aws`.
2. **`seguranca`** (needs: sintaxe): instalar `requirements.txt` → `pytest` (garante que os controles funcionam) → `python -m src.main terraform/aws` (**gate**: FAIL bloqueia).
3. **`checkov`** (needs: sintaxe): `pip install checkov` → `checkov -d terraform/aws --framework terraform --soft-fail`. É **informativo**: aponta mais itens, inclusive de severidade baixa, e não bloqueia. **O gate são os meus controles.** Justificar no README.
4. **`deploy`** (needs: seguranca, só na branch `main`): **apenas** `echo "Deploy conceitual – nada é provisionado"`. Nenhuma credencial, nenhum `plan`/`apply`.

Usar as versões estáveis atuais das actions oficiais (`actions/checkout`, `actions/setup-python`, `hashicorp/setup-terraform`).
Comentar no YAML **por que** cada etapa existe e por que nessa ordem (barato e rápido primeiro; segurança antes do deploy).

> **Importante para a demonstração:** como os `.tf` do desafio contêm problemas reais, o pipeline **ficará vermelho na etapa de segurança, por design**. Isso prova que o gate funciona. Documentar no README.

---

## 5. Documentos

### 5.1 `analise.md`
1. Escopo e método (as 5 perguntas).
2. **Tabela principal** com colunas: `Recurso | Arquivo | Status | Problema | Risco | Recomendação | Severidade`. Incluir **todos** os recursos, inclusive os conformes:
   - ❌ `aws_s3_bucket.exportacao_clientes`: 4 travas `false` + policy `Principal "*"` com `GetObject`/`ListBucket` → Crítica
   - ❌ `aws_security_group.app`: SSH (22) de `0.0.0.0/0` → Alta
   - ❌ `aws_db_instance.cadastro`: `publicly_accessible = true` em `subnets-publicas` → Alta
   - ❌ `aws_ebs_volume.logs_processamento`: `encrypted = false` → Média
   - ⚠️ Saída liberada para qualquer destino em `web`/`app`; RDS com chave KMS padrão; possível uso do usuário master pela aplicação; mesma CMK para S3 e EBS; `exportacao_clientes` sem versionamento nem KMS próprio; `relatorios_financeiros` sem logs de acesso nem política forçando HTTPS → Baixa
   - ✅ `relatorios_financeiros`, `web` (entrada 443), `monitoramento`, `dados_aplicacao`, `pagamentos`
3. Observações de projeto: `rds.tf` fora do padrão do `terraform fmt` (detectado e corrigido na cópia); versão do provider não fixada; `skip_final_snapshot = false` sem `final_snapshot_identifier`.
4. Itens **não avaliáveis** (fora dos arquivos): Security Groups dos bancos, subnets, parameter groups (TLS), permissões IAM.
5. Comparação com o Checkov: o que ele também achou e o que achou a mais (concordo/discordo).
6. Critério de severidade usado (ex.: Crítica = dado exposto sem depender de outra falha; Alta = exposição direta de serviço; Média = depende de falha prévia; Baixa = melhoria).

### 5.2 `evolucao.md` (máximo 1 página)
1. **O problema da escala:** dezenas de contas, times diferentes, mudanças fora do pipeline (console, drift).
2. **Defesa em camadas:**
   - *Antes do deploy (shift-left):* os mesmos controles + Checkov num **workflow reutilizável central**, com as políticas versionadas num repositório único.
   - *Preventivo:* **AWS Organizations** (contas em OUs, por exemplo Produção e Sandbox) + **SCPs** como guardrails (ex.: impedir que se desligue o bloqueio de acesso público do S3) + bloqueio de acesso público do S3 **no nível da conta**.
   - *Detectivo:* **AWS Config** com regras gerenciadas (nomes **confirmados** na documentação da AWS: `s3-bucket-level-public-access-prohibited`, `rds-instance-public-access-check`), conformance packs e agregador multi-conta.
   - *Detectivo/corretivo:* **Cloud Custodian**, com a mesma linguagem de política no pipeline (c7n-left) e no ambiente real; pode notificar ou remediar.
3. **Critérios e limitações:** custo do Config; risco de falsos positivos; processo de **exceção** (risco aceito com dono e prazo); remediação automática em produção exige cautela; SCP atua sobre ações de API, não sobre todo atributo de configuração.
4. **Como eu levaria para Azure:** Management Groups ≈ Organizations/OUs; **Azure Policy** com efeito `Deny` (preventivo) e `Audit` (detectivo): **um mesmo motor** cobre o que na AWS são SCP + Config; Defender for Cloud. Os cenários equivalentes existem no material Azure (Storage com acesso anônimo, SQL público com firewall `0.0.0.0–255.255.255.255`).

### 5.3 `uso-de-ia.md` (eu preencho; você só cria o esqueleto com as perguntas)
- Ferramentas utilizadas (Claude no chat para estudo e arquitetura; Claude Code para implementação).
- Em quais partes ajudou.
- O que revisei ou modifiquei.
- **Uma sugestão corrigida, descartada ou adaptada**: candidatos reais desta jornada:
  - A IA sugeriu o Security Group (SSH) como 2º controle; **escolhi o RDS** por expor diretamente dados pessoais.
  - Afirmações da IA (falha do `fmt` no `rds.tf`, IDs do Checkov, formato do `python-hcl2`) foram **verificadas executando** as ferramentas.
- O que aprendi.

### 5.4 `README.md`
1. Objetivo (2–3 linhas).
2. Abordagem em 3 etapas (seção 2 deste arquivo).
3. Pré-requisitos e instalação (venv, `pip install -r requirements.txt`; Checkov e Terraform opcionais).
4. Como executar: validação, testes, Checkov, sintaxe Terraform.
5. Exemplo de saída (PASS/FAIL) e significado do exit code.
6. Controles implementados (tabela: ID, o que verifica, severidade, por que foi escolhido, equivalente Checkov).
7. Decisões técnicas e alternativas consideradas (Checkov puro, OPA/Rego, c7n-left: por que não como principal).
8. Pipeline (fluxo + "fica vermelho por design").
9. Limitações e próximos passos (SG SSH, EBS, policy `Principal "*"`, `aws_rds_cluster_instance`, saída JSON/SARIF, exceções).
10. Links para `analise.md`, `evolucao.md`, `uso-de-ia.md`.

---

## 6. Fases de execução (pare e explique ao fim de cada uma)

| Fase | Entrega | Pronto quando |
|---|---|---|
| 1 | Estrutura de pastas, `.gitignore`, `requirements.txt`, cópia dos `.tf` em `terraform/aws/`, `terraform fmt` aplicado | `terraform fmt -check` e `validate` passam |
| 2 | Inspeção do formato do `python-hcl2` + `leitor_tf.py` | Dicionário mostrado e explicado |
| 3 | CTRL-AWS-002 (RDS) + exemplos + `test_rds.py` | `pytest` verde |
| 4 | CTRL-AWS-001 (S3) + exemplos + `test_s3.py` | `pytest` verde |
| 5 | `main.py` + `test_integracao.py` | Saída igual à da seção 4.5; exit code 1 |
| 6 | Rodar o Checkov e confirmar os IDs `A CONFIRMAR` | IDs atualizados na especificação e no README |
| 7 | `.github/workflows/security.yml` | YAML comentado e válido |
| 8 | `analise.md`, `evolucao.md`, esqueleto do `uso-de-ia.md`, `README.md` | Documentos completos |
| 9 | Revisão final pelo checklist (seção 7) | Todos os itens marcados |

---

## 7. Checklist final (do enunciado + critérios de avaliação)

- [x] Executa sem acessar AWS; nenhum `plan`/`apply`; nenhuma credencial ou segredo no repositório. *(busca por padrões de segredo sem ocorrências; ARNs usam a conta de exemplo 111122223333)*
- [x] 2 controles automatizados, no mesmo provedor (AWS).
- [x] Casos conformes e não conformes para cada controle (+ casos de borda). *(14 testes: ausente, trava parcial/ausente, nome literal, valor não verificável, exit codes 0/1/2)*
- [x] Mensagens de PASS/FAIL claras: problema, risco e remediação.
- [x] Pipeline com Commit → sintaxe → segurança → PASS/FAIL → deploy conceitual. *(etapas simuladas localmente; falta a 1ª execução real no GitHub Actions)*
- [x] Limitações e evoluções documentadas.
- [ ] `uso-de-ia.md` preenchido **por mim**.
- [x] **Coerência:** cada controle tem a mesma história em `analise.md` (risco) → código (regra) → teste (prova) → README (justificativa).
- [ ] Consigo explicar cada linha e fazer alterações ao vivo. Ensaiar:
  - adicionar um 3º controle (ex.: EBS `encrypted = false`); *(ensaiado numa cópia: 1 arquivo novo + 2 linhas no `main.py`; **lembrar de atualizar os números do `test_integracao.py`**)*
  - mudar a severidade ou a mensagem de um controle;
  - cobrir `aws_rds_cluster_instance`;
  - explicar por que o pipeline está vermelho e onde o deploy seria barrado.

---

## 8. Registro da fase 6: saída do Checkov (insumo para o `analise.md`)

Comando: `checkov -d terraform/aws --framework terraform --soft-fail` (Checkov 3.4.6, 14 recursos, 0 erros de parsing).
Resumo: **48 passed, 42 failed**.

| Recurso | Checks que falharam |
|---|---|
| `aws_s3_bucket.exportacao_clientes` | CKV2_AWS_6 (Public Access block), CKV_AWS_21 (versionamento), CKV_AWS_145 (KMS por padrão), CKV_AWS_18 (logs de acesso), CKV_AWS_144 (replicação entre regiões), CKV2_AWS_61 (lifecycle), CKV2_AWS_62 (notificação de eventos) |
| `aws_s3_bucket_public_access_block.exportacao_clientes` | CKV_AWS_53, CKV_AWS_54, CKV_AWS_55, CKV_AWS_56 |
| `aws_s3_bucket.relatorios_financeiros` | CKV_AWS_18 (logs de acesso), CKV_AWS_144, CKV2_AWS_61, CKV2_AWS_62 |
| `aws_security_group.app` | CKV_AWS_24 (22 a partir de 0.0.0.0/0), CKV_AWS_382 (egress liberado), CKV_AWS_23 (descrição), CKV2_AWS_5 (SG não anexado) |
| `aws_security_group.web` | CKV_AWS_382 (egress liberado), CKV_AWS_23, CKV2_AWS_5 |
| `aws_security_group.monitoramento` | CKV_AWS_23, CKV2_AWS_5 |
| `aws_ebs_volume.logs_processamento` | CKV_AWS_3 (sem criptografia), CKV_AWS_189 (sem CMK) |
| `aws_db_instance.cadastro` | CKV_AWS_17 (publicamente acessível), CKV_AWS_118, CKV_AWS_129, CKV_AWS_157, CKV_AWS_161, CKV_AWS_226, CKV_AWS_353, CKV2_AWS_60 |
| `aws_db_instance.pagamentos` | CKV_AWS_118, CKV_AWS_129, CKV_AWS_157, CKV_AWS_161, CKV_AWS_226, CKV_AWS_353, CKV2_AWS_60, CKV2_AWS_30 (query logging Postgres) |

Aprovados relevantes: CKV_AWS_17 em `pagamentos`; CKV_AWS_53–56 e CKV2_AWS_6 em `relatorios_financeiros`; CKV_AWS_24 em `web` e `monitoramento`; CKV_AWS_3 em `dados_aplicacao`.
O texto entre parênteses é uma tradução resumida do `check_name` que aparece na saída. Os IDs sem texto ainda precisam ser consultados pelo nome na saída do Checkov durante a análise (fase 8).
