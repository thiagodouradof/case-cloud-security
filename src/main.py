"""Executa os controles de segurança sobre arquivos Terraform.

Uso: python -m src.main terraform/aws   (aceita pasta ou arquivo .tf)

Exit code (é o que o pipeline usa para bloquear o deploy):
  0 = nenhum FAIL | 1 = ao menos um FAIL | 2 = erro de leitura ou de uso
"""

import os
import sys

from src.controles.rds_acesso_publico import verificar_rds_acesso_publico
from src.controles.s3_acesso_publico import verificar_s3_acesso_publico
from src.leitor_tf import carregar_arquivo, carregar_pasta

# Para adicionar um controle: importar a função e incluí-la nesta lista.
CONTROLES = [
    verificar_s3_acesso_publico,
    verificar_rds_acesso_publico,
]


def carregar(caminho):
    """Lê uma pasta inteira ou um único arquivo .tf."""
    if os.path.isdir(caminho):
        return carregar_pasta(caminho)
    return carregar_arquivo(caminho)


def executar_controles(config):
    """Roda todos os controles da lista e junta os resultados numa lista só."""
    resultados = []
    for controle in CONTROLES:
        resultados.extend(controle(config))
    return resultados


def main(argumentos):
    """Imprime uma linha por resultado e um resumo; devolve o exit code."""
    if len(argumentos) != 1:
        print("Uso: python -m src.main <pasta ou arquivo .tf>", file=sys.stderr)
        return 2

    caminho = argumentos[0]
    try:
        config = carregar(caminho)
    except ValueError as erro:
        print(f"ERRO de leitura: {erro}", file=sys.stderr)
        return 2

    resultados = executar_controles(config)
    total_fail = 0
    print(f"Validação de segurança – {caminho}\n")
    for r in resultados:
        print(f"{r['status']} [{r['controle']}][{r['severidade']}] {r['recurso']}: {r['mensagem']}")
        if r["status"] == "FAIL":
            total_fail += 1

    total_pass = len(resultados) - total_fail
    print(f"\nResumo: {len(resultados)} verificações | {total_pass} PASS | {total_fail} FAIL")
    if total_fail > 0:
        print("Resultado: FAIL – deploy bloqueado.")
        return 1
    print("Resultado: PASS – deploy liberado.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
