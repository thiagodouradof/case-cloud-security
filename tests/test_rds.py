"""Testes do CTRL-AWS-002 (RDS publicamente acessível)."""

import os

from src.controles.rds_acesso_publico import verificar_rds_acesso_publico
from src.leitor_tf import carregar_arquivo

PASTA_EXEMPLOS = os.path.join(os.path.dirname(__file__), "exemplos")


def avaliar_exemplo(nome_arquivo):
    """Lê um .tf de tests/exemplos e devolve o único resultado do controle."""
    config = carregar_arquivo(os.path.join(PASTA_EXEMPLOS, nome_arquivo))
    resultados = verificar_rds_acesso_publico(config)
    assert len(resultados) == 1
    return resultados[0]


def test_rds_conforme_passa():
    resultado = avaliar_exemplo("rds_conforme.tf")
    assert resultado["status"] == "PASS"
    assert resultado["recurso"] == "aws_db_instance.exemplo"


def test_rds_nao_conforme_falha():
    resultado = avaliar_exemplo("rds_nao_conforme.tf")
    assert resultado["status"] == "FAIL"
    assert resultado["controle"] == "CTRL-AWS-002"
    assert resultado["severidade"] == "ALTA"
    assert "Remediação" in resultado["mensagem"]


def test_dicionario_direto_sem_arquivo():
    # Objeto de configuração montado à mão, como no exemplo do enunciado.
    config = {
        "resource": [
            {"aws_db_instance": {"publico": {"publicly_accessible": True}}},
            {"aws_db_instance": {"privado": {"publicly_accessible": False}}},
        ]
    }
    resultados = verificar_rds_acesso_publico(config)
    status_por_recurso = {r["recurso"]: r["status"] for r in resultados}
    assert status_por_recurso == {
        "aws_db_instance.publico": "FAIL",
        "aws_db_instance.privado": "PASS",
    }


def test_valor_nao_verificavel_falha():
    # Uma variável não pode ser resolvida sem "terraform plan": por segurança, FAIL.
    config = {"resource": [{"aws_db_instance": {"x": {"publicly_accessible": "${var.publico}"}}}]}
    resultado = verificar_rds_acesso_publico(config)[0]
    assert resultado["status"] == "FAIL"
    assert "var.publico" in resultado["mensagem"]
