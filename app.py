from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)

# ESSA É A ÚNICA COISA QUE FUNCIONA NO VERCEL
CORS(app)  # ← LIBERA TUDO, SEM ORIGEM, SEM NADA

EXCEL_FILE = "Lotofácil.xlsx"

def carregar():
    if not os.path.exists(EXCEL_FILE):
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
    except:
        return None

@app.route('/api/resultados')
def resultados():
    dados = carregar()
    if not dados:
        return jsonify({"erro": "Excel não encontrado"}), 200  # ← 200 pra não dar 500
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
    
    ultimos = dados[:50]
    todos = [n for j in ultimos for n in j['numeros']]
    quentes = [n for n in range(1,26) if todos.count(n) > len(ultimos)*0.6][:8]
    
    def gerar():
        aposta = quentes[:random.randint(4,6)]
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
    return jsonify({"status": "online"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))