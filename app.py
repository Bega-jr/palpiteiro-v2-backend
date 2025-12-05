from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app, origins=["*"])  # ← AQUI TÁ O SEGREDO

EXCEL_FILE = "Lotofácil.xlsx"

def carregar():
    if not os.path.exists(EXCEL_FILE):
        print("Excel não encontrado!")
        return None
    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        dados = []
        for _, row in df.iterrows():
            try:
                numeros = [int(row[f'Bola{i}']) for i in range(1, 16)]
                dados.append({
                    'concurso': int(row['Concurso']),
                    'data': str(row['Data Sorteio']).split(' ')[0],
                    'numeros': sorted(numeros),
                })
            except:
                continue
        return sorted(dados, key=lambda x: x['concurso'], reverse=True)
    except Exception as e:
        print("Erro:", e)
        return None

@app.route('/api/resultados')
def resultados():
    dados = carregar()
    if not dados:
        return jsonify({"erro": "Excel não encontrado"}), 500
    ultimo = dados[0]
    return jsonify({
        "concurso": ultimo['concurso'],
        "data": ultimo": ultimo['data'],
        "numeros": ultimo['numeros']
    })

@app.route('/api/palpites-vip')
def palpites_vip():
    dados = carregar()
    if not dados:
        return jsonify({"erro": "Sem dados"}), 503

    ultimos = dados[:100]
    todos_numeros = [n for jogo in ultimos for n in jogo['numeros']]
    contagem = {n: todos_numeros.count(n) for n in range(1, 26)}

    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:8]
    quentes_nums = [n for n, c in quentes]

    def gerar():
        aposta = quentes_nums[:random.randint(4, 6)]
        restantes = [n for n in range(1, 26) if n not in aposta]
        while len(aposta) < 15:
            aposta.append(random.choice(restantes))
            restantes.remove(aposta[-1])
        return sorted(aposta)

    apostas = [gerar() for _ in range(7)]

    return jsonify({
        "quentes": quentes_nums,
        "apostas": apostas,
        "gerado_em": "agora"
    })

@app.route('/')
def home():
    return jsonify({"status": "online", "excel_ok": os.path.exists(EXCEL_FILE)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))