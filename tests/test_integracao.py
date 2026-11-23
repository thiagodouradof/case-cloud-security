"""Testes de integração: leitor + controles + runner sobre os .tf reais do desafio."""

import os

from src.main import carregar, executar_controles, main

RAIZ = os.path.dirname(os.path.dirname(__file__))
PASTA_DESAFIO = os.path.join(RAIZ, "terraform", "aws")
PASTA_EXEMPLOS = os.path.join(RAIZ, "tests", "exemplos")


def test_somente_exportacao_clientes_e_cadastro_falham():
    resultados = executar_controles(carregar(PASTA_DESAFIO))
    falhas = sorted(r["recurso"] for r in resultados if r["status"] == "FAIL")
    assert len(resultados) == 4
    assert falhas == ["aws_db_instance.cadastro", "aws_s3_bucket.exportacao_clientes"]


def test_desafio_bloqueia_deploy_com_exit_code_1(capsys):
    assert main([PASTA_DESAFIO]) == 1
    saida = capsys.readouterr().out
    assert "Resumo: 4 verificações | 2 PASS | 2 FAIL" in saida
    assert "Resultado: FAIL – deploy bloqueado." in saida


def test_arquivo_conforme_libera_deploy_com_exit_code_0():
    assert main([os.path.join(PASTA_EXEMPLOS, "s3_conforme.tf")]) == 0


def test_erro_de_leitura_devolve_exit_code_2(capsys):
    assert main(["caminho_que_nao_existe.tf"]) == 2
    assert "ERRO de leitura" in capsys.readouterr().err
