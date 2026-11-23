"""CTRL-AWS-002: instância RDS publicamente acessível.

Regra:
  publicly_accessible = true   -> FAIL
  publicly_accessible = false  -> PASS
  atributo ausente             -> PASS (o padrão do provider AWS é false)
  qualquer outro valor         -> FAIL (ex.: var.publico; não dá para provar que é seguro)
"""

from src.leitor_tf import listar_recursos

CONTROLE = "CTRL-AWS-002"
SEVERIDADE = "ALTA"

MENSAGEM_FAIL = (
    "banco publicamente acessível (publicly_accessible = true). "
    "O banco recebe IP público e fica a uma única camada (Security Group) da internet. "
    "Remediação: definir publicly_accessible = false e usar subnets privadas; "
    "acesso administrativo via VPN/bastion/SSM."
)


def verificar_rds_acesso_publico(config):
    """Avalia cada aws_db_instance e devolve uma lista de resultados PASS/FAIL."""
    resultados = []

    for nome, atributos in listar_recursos(config, "aws_db_instance"):
        valor = atributos.get("publicly_accessible")

        if valor is True:
            status = "FAIL"
            mensagem = MENSAGEM_FAIL
        elif valor is False:
            status = "PASS"
            mensagem = "banco não é publicamente acessível."
        elif valor is None:
            status = "PASS"
            mensagem = "banco não é publicamente acessível (atributo ausente; o padrão é false)."
        else:
            status = "FAIL"
            mensagem = (
                f"valor de publicly_accessible não verificável estaticamente ({valor}). "
                "Remediação: definir publicly_accessible = false de forma explícita."
            )

        resultados.append({
            "controle": CONTROLE,
            "recurso": f"aws_db_instance.{nome}",
            "status": status,
            "severidade": SEVERIDADE,
            "mensagem": mensagem,
        })

    return resultados
