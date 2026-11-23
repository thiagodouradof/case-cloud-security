"""Testes do CTRL-AWS-001 (S3 sem bloqueio de acesso público)."""

import os

from src.controles.s3_acesso_publico import verificar_s3_acesso_publico
from src.leitor_tf import carregar_arquivo

PASTA_EXEMPLOS = os.path.join(os.path.dirname(__file__), "exemplos")


def avaliar_exemplo(nome_arquivo):
    """Lê um .tf de tests/exemplos e devolve o único resultado do controle."""
    config = carregar_arquivo(os.path.join(PASTA_EXEMPLOS, nome_arquivo))
    resultados = verificar_s3_acesso_publico(config)
    assert len(resultados) == 1
    return resultados[0]


def test_s3_conforme_passa():
    resultado = avaliar_exemplo("s3_conforme.tf")
    assert resultado["status"] == "PASS"
    assert resultado["recurso"] == "aws_s3_bucket.exemplo"


def test_s3_nao_conforme_lista_as_4_travas():
    resultado = avaliar_exemplo("s3_nao_conforme.tf")
    assert resultado["status"] == "FAIL"
    assert resultado["controle"] == "CTRL-AWS-001"
    assert resultado["severidade"] == "CRITICA"
    assert ("Travas desligadas: block_public_acls, block_public_policy, "
            "ignore_public_acls, restrict_public_buckets.") in resultado["mensagem"]


def test_s3_trava_parcial_lista_so_a_aberta():
    resultado = avaliar_exemplo("s3_trava_parcial.tf")
    assert resultado["status"] == "FAIL"
    assert "Travas desligadas: block_public_policy." in resultado["mensagem"]


def test_s3_sem_bloqueio_falha():
    resultado = avaliar_exemplo("s3_sem_bloqueio.tf")
    assert resultado["status"] == "FAIL"
    assert "nenhum bloqueio" in resultado["mensagem"]


def test_dicionario_direto_sem_arquivo():
    # Objeto de configuração montado à mão, como no exemplo do enunciado.
    # - "literal": o bloqueio aponta para o NOME do bucket, e não para uma referência;
    # - "trava_ausente": restrict_public_buckets não foi declarada (conta como desligada);
    # - "sem_bloqueio": não há bloqueio apontando para ele.
    config = {
        "resource": [
            {"aws_s3_bucket": {"literal": {"bucket": "acme-literal"}}},
            {"aws_s3_bucket_public_access_block": {"b1": {
                "bucket": "acme-literal",
                "block_public_acls": True, "block_public_policy": True,
                "ignore_public_acls": True, "restrict_public_buckets": True,
            }}},
            {"aws_s3_bucket": {"trava_ausente": {"bucket": "acme-trava-ausente"}}},
            {"aws_s3_bucket_public_access_block": {"b2": {
                "bucket": "${aws_s3_bucket.trava_ausente.id}",
                "block_public_acls": True, "block_public_policy": True, "ignore_public_acls": True,
            }}},
            {"aws_s3_bucket": {"sem_bloqueio": {"bucket": "acme-sem-bloqueio"}}},
        ]
    }
    resultados = {r["recurso"]: r for r in verificar_s3_acesso_publico(config)}

    assert resultados["aws_s3_bucket.literal"]["status"] == "PASS"
    assert resultados["aws_s3_bucket.trava_ausente"]["status"] == "FAIL"
    assert "Travas desligadas: restrict_public_buckets." in resultados["aws_s3_bucket.trava_ausente"]["mensagem"]
    assert resultados["aws_s3_bucket.sem_bloqueio"]["status"] == "FAIL"
