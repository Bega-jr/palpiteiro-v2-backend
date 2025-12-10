from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
import random

app = Flask(__name__)
CORS(app)

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
                    'numeros': sorted(numeros),
                    'ganhadores_15': int(row.get('Ganhadores 15 acertos', 0)),
                    'premio_15': str(row.get('Rateio 15 acertos', 'R$0,00')),
                    'ganhadores_14': int(row.get('Ganhadores 14 acertos', 0)),
                    'premio_14': str(row.get('Rateio 14 acertos', 'R$0,00')),
                    'ganhadores_13': int(row.get('Ganhadores 13 acertos', 0)),
                    'premio_13': str(row.get('Rateio 13 acertos', 'R$0,00')),
                    'ganhadores_12': int(row.get('Ganhadores 12 acertos', 0)),
                    'premio_12': str(row.get('Rateio 12 acertos', 'R$0,00')),
                    'ganhadores_11': int(row.get('Ganhadores 11 acertos', 0)),
                    'premio_11': str(row.get('Rateio 11 acertos', 'R$0,00')),
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
    faixas = [
        {"faixa": "15 acertos", "ganhadores": ultimo['ganhadores_15'], "premio": ultimo['premio_15']},
        {"faixa": "14 acertos", "ganhadores": ultimo['ganhadores_14'], "premio": ultimo['premio_14']},
        {"faixa": "13 acertos", "ganhadores": ultimo['ganhadores_13'], "premio": ultimo['premio_13']},
        {"faixa": "12 acertos", "ganhadores": ultimo['ganhadores_12'], "premio": ultimo['premio_12']},
        {"faixa": "11 acertos", "ganhadores": ultimo['ganhadores_11'], "premio": ultimo['premio_11']},
    ]
    return jsonify({
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": ultimo['numeros'],
        "ganhadores": faixas
    })

@app.route('/api/estatisticas')
def estatisticas():
    dados = carregar()
    if not dados:
        return jsonify({"erro": "Sem dados"}), 503

    ultimos_50 = dados[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1

    mais = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    menos = sorted(contagem.items(), key=lambda x: x[1])[:10]

    todos = set(range(1,26))
    recentes = set()
    for j in dados[:20]:
        recentes.update(j['numeros'])
    atrasados = sorted(todos - recentes)

    return jsonify({
        "maisSorteados": [{"numero": n, "vezes": c} for n,c in mais],
        "menosSorteados": [{"numero": n, "vezes": c} for n,c in menos],
        "atrasados": atrasados
    })

@app.route('/api/palpites-vip')
def palpites_vip():
    dados = carregar()
    if not dados:
        return jsonify({"erro": "Sem dados"}), 503

    ultimos = dados[:50]
    contagem = {}
    for j in ultimos:
        for n in j['numeros']:
            contagem[n] = contagem.get(n, 0) + 1
    quentes = [n for n,c in sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:8]]

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
    return jsonify({"status": "Palpiteiro V2 - Online", "excel_ok": os.path.exists(EXCEL_FILE)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))