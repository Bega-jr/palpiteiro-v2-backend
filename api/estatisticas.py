# api/estatisticas.py
from flask import Flask, jsonify
from flask_cors import CORS
from excel_manager import carregar_excel_struct
from api_client import obter_dados_externos  # função de baixo-level que tenta API externa
import pandas as pd

app = Flask(__name__)
CORS(app)

def calcular_estatisticas_from_df(df):
    if df is None or df.empty:
        return {}

    ultimos_50 = df.sort_values("Concurso", ascending=False).head(50)
    all_numbers = []
    for row in ultimos_50["numeros"]:
        all_numbers.extend(row if isinstance(row, list) else [])

    s = pd.Series(all_numbers)
    freq = s.value_counts().sort_values(ascending=False)

    mais = [{"numero": int(idx), "vezes": int(v)} for idx, v in freq.items()][:10]
    menos = [{"numero": int(idx), "vezes": int(v)} for idx, v in freq.items()][-10:]

    recentes = set()
    for row in df.sort_values("Concurso", ascending=False).head(20)["numeros"]:
        recentes.update(row if isinstance(row, list) else [])
    atrasados = sorted(list(set(range(1, 26)) - recentes))

    soma_media = None
    try:
        soma_lista = [sum(row) for row in df["numeros"].apply(lambda x: x if isinstance(x, list) else [])]
        soma_media = float(pd.Series(soma_lista).mean()) if soma_lista else None
    except Exception:
        soma_media = None

    pares_impares = {"pares": None, "impares": None}
    try:
        pares = []
        impares = []
        for row in df["numeros"].apply(lambda x: x if isinstance(x, list) else []):
            p = sum(1 for n in row if n % 2 == 0)
            i = len(row) - p
            pares.append(p)
            impares.append(i)
        pares_impares["pares"] = float(pd.Series(pares).mean()) if pares else None
        pares_impares["impares"] = float(pd.Series(impares).mean()) if impares else None
    except Exception:
        pass

    finais = {}
    for n in range(10):
        finais[n] = sum(1 for num in all_numbers if num % 10 == n)

    return {
        "maisSorteados": mais,
        "menosSorteados": menos,
        "atrasados": atrasados,
        "somaMedia": soma_media,
        "paresImpares": pares_impares,
        "finais": finais,
        "concursos_total": int(df.shape[0])
    }

@app.route("/", methods=["GET"])
def estatisticas_route():
    # Tenta apenas ler Excel (padrão). Poderíamos tentar API externa e compor, mas Excel é fonte única aqui.
    df = carregar_excel_struct()
    if df is None:
        return jsonify({"erro": "Sem dados"}), 503
    stats = calcular_estatisticas_from_df(df)
    return jsonify(stats)
