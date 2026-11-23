"""CTRL-AWS-001: bucket S3 sem bloqueio de acesso público completo.

Regra: cada aws_s3_bucket precisa de um aws_s3_bucket_public_access_block
com as 4 travas em true. Trava ausente conta como desligada (o padrão é false).
"""

from src.leitor_tf import listar_recursos

CONTROLE = "CTRL-AWS-001"
SEVERIDADE = "CRITICA"

TRAVAS = ["block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets"]

RISCO_E_REMEDIACAO = (
    'Risco: o bucket pode ser exposto à internet (ex.: policy com Principal "*"). '
    "Remediação: definir as 4 travas como true; para compartilhamento externo, usar URLs pré-assinadas."
)


def encontrar_bloqueio(nome, nome_literal, bloqueios):
    """Devolve o bloqueio que aponta para o bucket, ou None se não houver.

    O atributo 'bucket' do bloqueio pode ser uma referência (aws_s3_bucket.N.id)
    ou o nome literal do bucket ("acme-meu-bucket").
    """
    for bloqueio in bloqueios:
        alvo = bloqueio.get("bucket")
        if isinstance(alvo, str) and alvo.startswith(f"aws_s3_bucket.{nome}."):
            return bloqueio
        if nome_literal is not None and alvo == nome_literal:
            return bloqueio
    return None


def verificar_s3_acesso_publico(config):
    """Avalia cada aws_s3_bucket e devolve uma lista de resultados PASS/FAIL."""
    bloqueios = [atributos for _, atributos in listar_recursos(config, "aws_s3_bucket_public_access_block")]
    resultados = []

    for nome, atributos in listar_recursos(config, "aws_s3_bucket"):
        bloqueio = encontrar_bloqueio(nome, atributos.get("bucket"), bloqueios)

        if bloqueio is None:
            status = "FAIL"
            mensagem = "nenhum bloqueio de acesso público declarado. " + RISCO_E_REMEDIACAO
        else:
            abertas = [trava for trava in TRAVAS if bloqueio.get(trava) is not True]
            if abertas:
                status = "FAIL"
                mensagem = (
                    "bloqueio de acesso público incompleto. "
                    f"Travas desligadas: {', '.join(abertas)}. " + RISCO_E_REMEDIACAO
                )
            else:
                status = "PASS"
                mensagem = "bloqueio de acesso público completo."

        resultados.append({
            "controle": CONTROLE,
            "recurso": f"aws_s3_bucket.{nome}",
            "status": status,
            "severidade": SEVERIDADE,
            "mensagem": mensagem,
        })

    return resultados
