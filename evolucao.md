# Evolução para um ambiente com múltiplas contas AWS

## 1. O problema da escala

Com dezenas de contas e times diferentes, um único pipeline num único repositório não basta:
- cada time tem o próprio repositório e pode copiar, alterar ou desligar as verificações;
- há mudanças que **não passam pelo pipeline**, feitas pelo console, pela CLI ou em incidentes (*drift*);
- uma conta nova já precisa nascer protegida, antes de existir qualquer código.

Por isso, a validação estática vira **uma camada entre várias**.

## 2. Defesa em camadas

| Camada | Quando atua | Como |
|---|---|---|
| **Antes do deploy** (*shift-left*) | No commit ou PR | Os mesmos controles + Checkov num **workflow reutilizável central** (`workflow_call`), com as políticas versionadas num **repositório único**. Cada time chama o workflow; ninguém copia regras. |
| **Preventivo** | Na chamada de API | **AWS Organizations** com contas em OUs (ex.: *Produção* e *Sandbox*) + **SCPs** como guardrails (ex.: negar `s3:PutAccountPublicAccessBlock` e `s3:PutBucketPublicAccessBlock` para quem não é do time de plataforma) + **bloqueio de acesso público do S3 no nível da conta**, que vale mesmo para buckets criados fora do Terraform. |
| **Detectivo** | Depois da mudança, contínuo | **AWS Config** com regras gerenciadas: `s3-bucket-level-public-access-prohibited` (CTRL-AWS-001) e `rds-instance-public-access-check` (CTRL-AWS-002), confirmadas na documentação da AWS. Regras agrupadas em **conformance packs** e um **agregador multi-conta** para a visão central. |
| **Detectivo / corretivo** | Contínuo | **Cloud Custodian**: a mesma linguagem de política roda no pipeline (c7n-left, sobre o Terraform) e no ambiente real. Pode só notificar ou também remediar (ex.: religar o bloqueio público). |

Os dois controles deste desafio aparecem em todas as camadas: no PR (meu código), na API (SCP e bloqueio da conta) e no ambiente real (Config/Custodian).

## 3. Critérios e limitações

- **Custo:** o AWS Config cobra por item de configuração registrado e por avaliação de regra; em muitas contas isso pesa. Começar pelas regras de maior risco.
- **Falsos positivos:** um bucket de site estático **deve** ser público. Sem tratamento, o time aprende a ignorar o alerta.
- **Processo de exceção:** risco aceito formalmente, com **dono, justificativa e prazo de expiração**, registrado e revisado (ex.: parâmetro `excludedPublicBuckets` do Config, `skip` com comentário no Checkov).
- **Remediação automática em produção exige cautela:** começar notificando, medir os falsos positivos e só depois automatizar a correção, de preferência em Sandbox primeiro.
- **SCP atua sobre ações de API, não sobre todo atributo de configuração:** a SCP consegue negar a chamada que desliga o bloqueio, mas não "olha dentro" de toda configuração. Por isso, ela não substitui o detectivo.

## 4. Como eu levaria para Azure

- **Management Groups** ≈ Organizations/OUs: a hierarquia onde as políticas são herdadas.
- **Azure Policy** com efeito **`Deny`** (preventivo) e **`Audit`** (detectivo): **um mesmo motor** cobre o que, na AWS, fica dividido entre SCP e Config. Policies agrupadas em *initiatives* (≈ conformance packs).
- **Microsoft Defender for Cloud:** a visão de postura e as recomendações (≈ Security Hub).
- Os cenários equivalentes existem no material Azure do desafio: **Storage Account com acesso anônimo** (≈ CTRL-AWS-001) e **SQL público com regra de firewall `0.0.0.0–255.255.255.255`** (≈ CTRL-AWS-002).
