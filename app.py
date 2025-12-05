from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
import random

app = Flask(__name__)
CORS(app)  # ← LIBERA TUDO

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
                    'numeros': numeros
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
        return jsonify({"concurso": 3552, "data": "05/12/2025", "numeros": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,25]})
    return jsonify({
        "concurso": dados[0]['concurso'],
        "data": dados[0]['data'],
        "numeros": dados[0]['numeros']
    })

@app.route('/api/palpites-vip')
def palpites_vip():
    dados = carregar()
    if not dados:
        return jsonify({"erro": "Sem dados"}), 200

    # 8 números mais quentes
    ultimos = dados[:50]
    todos = [n for j in ultimos for n in j['numeros']]
    quentes = []
    for n in range(1, 26):
        if todos.count(n) > 28:
            quentes.append(n)
    quentes = quentes[:8] or [3,5,7,11,13,15,17,25]

    def gerar():
        aposta = quentes[:random.randint(5,7)]
        while len(aposta) < 15:
            n = random.randint(1,25)
            if n not in aposta:
                aposta.append(n)
        return sorted(aposta)

    return jsonify({
        "quentes": quentes,
        "apostas": [gerar() for _ in range(7)]
    })

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - Online", "hora": "agora"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))