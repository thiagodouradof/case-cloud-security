"""Leitura de arquivos Terraform (.tf) com a biblioteca python-hcl2.

Toda a "esquisitice" do formato do python-hcl2 fica neste arquivo.
Os controles recebem atributos já limpos e não precisam saber como o .tf foi lido.
"""

import os

import hcl2


def carregar_arquivo(caminho):
    """Lê um arquivo .tf e devolve o dicionário gerado pelo python-hcl2."""
    try:
        # "utf-8-sig" aceita arquivos com ou sem BOM (editores do Windows costumam gravar BOM)
        with open(caminho, encoding="utf-8-sig") as arquivo:
            return hcl2.load(arquivo)
    except OSError:
        raise ValueError(f"não foi possível abrir o arquivo: {caminho}")
    except Exception as erro:
        raise ValueError(f"HCL inválido em {caminho}: {erro}")


def carregar_pasta(caminho):
    """Lê todos os .tf de uma pasta e junta os blocos 'resource' num só dicionário.

    O Terraform trata a pasta inteira como um único projeto, então fazemos o mesmo.
    """
    if not os.path.isdir(caminho):
        raise ValueError(f"pasta não encontrada: {caminho}")

    recursos = []
    for nome_arquivo in sorted(os.listdir(caminho)):
        if nome_arquivo.endswith(".tf"):
            config = carregar_arquivo(os.path.join(caminho, nome_arquivo))
            recursos.extend(config.get("resource", []))

    if not recursos:
        raise ValueError(f"nenhum recurso encontrado em arquivos .tf de: {caminho}")
    return {"resource": recursos}


def listar_recursos(config, tipo):
    """Devolve [(nome, atributos), ...] de todos os recursos de um tipo.

    Formato observado (python-hcl2 8.2.0): 'resource' é uma LISTA, com um
    dicionário por bloco, e o tipo e o nome chegam com aspas:
        {"resource": [{'"aws_db_instance"': {'"cadastro"': {...atributos...}}}]}
    """
    encontrados = []
    for bloco in config.get("resource", []):
        for tipo_bloco, recursos_do_tipo in bloco.items():
            if limpar_valor(tipo_bloco) != tipo:
                continue
            for nome, atributos in recursos_do_tipo.items():
                encontrados.append((limpar_valor(nome), limpar_valor(atributos)))
    return encontrados


def limpar_valor(valor):
    """Normaliza um valor lido pelo python-hcl2.

    - '"texto"'                  -> 'texto'   (remove as aspas que a biblioteca mantém)
    - '${aws_s3_bucket.x.id}'    -> 'aws_s3_bucket.x.id'   (remove o ${ } das referências)
    - '"true"' / '"false"'       -> True / False   (o Terraform aceita booleano como texto)
    - dicionários e listas: limpa cada item (blocos internos, tags, listas de IDs)
    - remove a chave '__is_block__', que é só um marcador interno da biblioteca
    """
    if isinstance(valor, dict):
        limpo = {}
        for chave, item in valor.items():
            if chave != "__is_block__":
                limpo[limpar_valor(chave)] = limpar_valor(item)
        return limpo

    if isinstance(valor, list):
        return [limpar_valor(item) for item in valor]

    if not isinstance(valor, str):
        return valor  # números e booleanos já chegam no tipo certo

    if len(valor) >= 2 and valor.startswith('"') and valor.endswith('"'):
        valor = valor[1:-1]
    if valor.startswith("${") and valor.endswith("}"):
        valor = valor[2:-1]
    if valor == "true":
        return True
    if valor == "false":
        return False
    return valor
