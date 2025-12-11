# api/resultados.py
from flask import Flask, jsonify
from flask_cors import CORS
from excel_manager import carregar_excel_struct, listar_concursos_dict
from estatisticas import obter_dados_api as obter_api_externa

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def resultados():
    """
    1) Tenta obter dados atualizados da API externa (padronizados por estatisticas.obter_dados_api).
    2) Se obteve, devolve esses dados.
    3) Se não, usa o Excel local (fallback).
    """
    try:
        api_data = obter_api_externa()
        if api_data and api_data.get("concurso"):
            # já padronizado
            # espera-se que api_data contenha 'concurso', 'data', 'numeros' e 'ganhadores' (opcional)
            resp = {
                "ultimo_concurso": int(api_data.get("concurso")),
                "data_ultimo": api_data.get("data") or api_data.get("dataApuracao") or "",
                "ultimos_numeros": api_data.get("numeros") or api_data.get("dezenas") or [],
                "ganhadores": api_data.get("ganhadores") or []
            }
            return jsonify(resp)
    except Exception as e:
        app.logger.warning("Erro ao chamar API externa: %s", e)

    # fallback: ler Excel local
    df_list = listar_concursos_dict()
    if not df_list:
        return jsonify({"erro": "Sem dados disponíveis"}), 503

    ultimo = df_list[0]
    faixas = [
        {"faixa": "15 acertos", "ganhadores": ultimo.get("ganhadores_15", 0), "premio": ultimo.get("premio_15", "R$0,00")},
        {"faixa": "14 acertos", "ganhadores": ultimo.get("ganhadores_14", 0), "premio": ultimo.get("premio_14", "R$0,00")},
        {"faixa": "13 acertos", "ganhadores": ultimo.get("ganhadores_13", 0), "premio": ultimo.get("premio_13", "R$0,00")},
        {"faixa": "12 acertos", "ganhadores": ultimo.get("ganhadores_12", 0), "premio": ultimo.get("premio_12", "R$0,00")},
        {"faixa": "11 acertos", "ganhadores": ultimo.get("ganhadores_11", 0), "premio": ultimo.get("premio_11", "R$0,00")},
    ]
    return jsonify({
        "ultimo_concurso": ultimo.get("concurso"),
        "data_ultimo": ultimo.get("data"),
        "ultimos_numeros": ultimo.get("numeros", []),
        "ganhadores": faixas
    })
