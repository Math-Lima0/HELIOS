"""
sistema_arquivos.py
===================
Módulo responsável pela persistência de dados do Projeto H.E.L.I.O.S.
Salva e carrega o estado completo do objeto Resultado em formato .helios (JSON).
"""

import json
import os
from dataclasses import asdict
from motor_volpiano import Resultado, Saida, ResultadoSaida

def salvar_projeto_helios(resultado: Resultado, caminho_arquivo: str, nome_projeto: str = "Novo Projeto"):
    """
    Serializa o objeto Resultado completo e adiciona os metadados do Pantheon.
    """
    # 1. Garante que a extensão do arquivo seja .helios
    if not caminho_arquivo.endswith('.helios'):
        caminho_arquivo += '.helios'
        
    try:
        # 2. Converte a dataclass complexa num dicionário nativo do Python
        dados_projeto = asdict(resultado)
        
        # 3. Empacota os dados com os metadados do Santuário do Pantheon
        pacote = {
            "metadata": {
                "pantheon_module": "H.E.L.I.O.S.",
                "version": "1.0",
                "project_name": nome_projeto
            },
            "data": dados_projeto
        }
        
        # 4. Grava o JSON estruturado no arquivo
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(pacote, f, indent=2, ensure_ascii=False)
            
        return True, caminho_arquivo
    except Exception as e:
        return False, str(e)


def carregar_projeto_helios(caminho_arquivo: str):
    """
    Lê um arquivo .helios e reconstrói o objeto Resultado completo,
    reinstanciando as dataclasses internas.
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            pacote = json.load(f)
            
        # Validação básica de segurança do cabeçalho
        if pacote.get("metadata", {}).get("pantheon_module") != "H.E.L.I.O.S.":
            raise ValueError("O arquivo fornecido não é um projeto H.E.L.I.O.S. válido.")
            
        raw_data = pacote["data"]
        
        # 1. Reconstruir a lista de objetos Saida originais
        lista_saidas = []
        for s in raw_data["saidas"]:
            lista_saidas.append(Saida(tipo=s["tipo"], Vout=s["Vout"], IL=s["IL"], R2=s["R2"]))
            
        # 2. Reconstruir a lista de objetos ResultadoSaida calculados
        lista_res_saidas = []
        for rs in raw_data["res_saidas"]:
            lista_res_saidas.append(ResultadoSaida(**rs))
            
        # 3. Remover as listas brutas do dicionário para não chocar no construtor da dataclass
        del raw_data["saidas"]
        del raw_data["res_saidas"]
        
        # 4. Instanciar o objeto Resultado principal com os tipos corretos reconstruídos
        resultado_objeto = Resultado(
            saidas=lista_saidas,
            res_saidas=lista_res_saidas,
            **raw_data
        )
        
        nome_projeto = pacote["metadata"]["project_name"]
        return True, resultado_objeto, nome_projeto
        
    except Exception as e:
        return False, str(e), ""