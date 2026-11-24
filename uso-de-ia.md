# Uso de IA neste desafio

Usei a IA como **par de programação** (*pair programming*): eu conduzia as decisões e ela atuava como colega para discutir arquitetura, explicar conceitos e escrever código que eu revisava, executava e questionava. Nenhuma afirmação da IA entrou no projeto sem ser verificada executando a ferramenta correspondente.

## 1. Ferramentas utilizadas

- **Claude (chat):** estudo de conceitos (Terraform/HCL, análise estática, Checkov, OPA, Cloud Custodian, AWS Organizations, SCP, Config) e discussão de arquitetura antes de escrever código.
- **Claude Code:** implementação em fases, com uma parada ao fim de cada fase para eu revisar, pedir explicações e aprovar.

## 2. Em quais partes a IA ajudou

| Parte | Como a IA ajudou | Meu papel |
|---|---|---|
| **Compreensão de conceitos** | Explicou como o Terraform lê uma pasta como um único projeto, o que é o `public_access_block` do S3, o que `publicly_accessible` faz no RDS, a diferença entre controle preventivo e detectivo | Fazer perguntas até conseguir explicar com as minhas palavras |
| **Análise dos arquivos** | Nas 3 etapas da análise (entender o Terraform, ler cada recurso, mapear o risco), respondeu às minhas perguntas sobre cada atributo e o porquê de ele ser ou não um risco | Ler os arquivos, aplicar as 5 perguntas e decidir o status de cada recurso |
| **Critério de severidade** | Ajudou a montar a escala Crítica / Alta / Média / Baixa e a ideia de medir "quantas falhas faltam para o dado vazar" | Aplicar o critério a cada achado e conferir se a ordem fazia sentido |
| **Arquitetura** | Discutimos as alternativas (Checkov puro, OPA/Rego, c7n-left, Python + python-hcl2) e como separar leitura de regra (o controle recebe um dicionário, não um arquivo) | Escolher a abordagem pelos critérios de simplicidade e de conseguir explicar cada linha |
| **Decisões** | Apresentou os prós e contras de cada escolha (qual controle automatizar, severidade, Checkov como gate ou informativo, o que fazer com um valor não verificável) | Decidir e justificar |
| **Código e testes** | Escreveu o leitor, os 2 controles, o runner, os exemplos `.tf` e os testes, explicando cada função | Revisar, rodar, pedir ajustes e reescrever à mão no meu ambiente |
| **Evolução multi-conta e Azure** | Explicou AWS Organizations, SCP, AWS Config e Cloud Custodian, e ajudou a pensar o paralelo com Azure (Management Groups, Azure Policy) | Escolher o que entra no `evolucao.md` e escrever só o que consigo explicar |
| **Pipeline e documentação** | Rascunhou o workflow do GitHub Actions e os documentos | Conferir coerência e ajustar o texto |

## 3. O que revisei ou modifiquei

- Defini o **plano em fases**, com critério de pronto, e só avancei com tudo verde (`terraform validate`, `pytest`, exit code esperado).
- Exigi que o **formato real do `python-hcl2` fosse mostrado antes** de escrever o leitor. O formato observado era diferente do esperado: tipo e nome vêm com aspas, `resource` é uma lista e as referências vêm como `${...}`.
- Revisei se cada controle conta **a mesma história** na análise (risco), no código (regra), no teste (prova) e no README (justificativa).
- Mantive o código propositalmente simples (sem classes, funções pequenas, nomes em português) para conseguir reescrevê-lo e alterá-lo ao vivo.

## 4. O que aprendi

- **Técnico:** como ler Terraform como dado (HCL → dicionário), escrever um controle de segurança com regra explícita e pensar em camadas (shift-left, preventivo, detectivo) quando o ambiente cresce para muitas contas.
- **Sobre segurança:** a severidade depende de **quantas falhas faltam** para o dado vazar. Uma ferramenta de mercado aponta muito, mas cabe a mim priorizar e dizer o que é ruído.
- **Sobre usar IA:** ela acelera muito, mas **erra com confiança** em detalhes como formatos de biblioteca, IDs e versões. O valor está em usá-la como par: perguntar o porquê, pedir alternativas e **verificar executando** antes de confiar.
