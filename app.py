from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app, origins=["https://palpiteirov2.netlify.app", "*"])

# EXCEL NA RAIZ
EXCEL_FILE = "Lotofácil.xlsx"

def carregar_lotofacil():
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
                    'numeros': numeros,
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
                    'arrecadacao': str(row.get('Arrecadacao Total', 'R$0,00')),
                    'estimativa': str(row.get('Estimativa Prêmio', 'R$0,00')),
                    'acumulado_15': 'SIM' in str(row.get('Acumulado 15 acertos', ''))
                })
            except:
                continue
        return sorted(dados, key=lambda x: x['concurso'], reverse=True)
    except Exception as e:
        print("Erro ao ler Excel:", e)
        return None

@app.route('/api/resultados')
def resultados():
    dados = carregar_lotofacil()
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
        "ganhadores": faixas,
        "arrecadacao": ultimo['arrecadacao'],
        "estimativa_proximo": ultimo['estimativa'],
        "acumulou": ultimo['acumulado_15']
    })

@app.route('/api/estatisticas')
def estatisticas():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Dados indisponíveis"}), 503

    ultimos_50 = dados[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1

    mais_sorteados = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    menos_sorteados = sorted(contagem.items(), key=lambda x: x[1])[:10]
    moda = mais_sorteados[0][0] if mais_sorteados else 1

    todos = set(range(1, 26))
    recentes = set()
    for jogo in dados[:20]:
        recentes.update(jogo['numeros'])
    atrasados = sorted(todos - recentes)

    soma_media = round(sum(sum(j['numeros']) for j in dados) / len(dados))
    pares = sum(1 for j in dados for n in j['numeros'] if n % 2 == 0) // len(dados)
    impares = 15 - pares

    finais = {i: 0 for i in range(10)}
    for j in dados:
        for n in j['numeros']:
            finais[n % 10] += 1

    return jsonify({
        "maisSorteados": [{"numero": n, "vezes": c} for n, c in mais_sorteados],
        "menosSorteados": [{"numero": n, "vezes": c} for n, c in menos_sorteados],
        "moda": moda,
        "atrasados": atrasados,
        "somaMedia": soma_media,
        "paresImpares": {"pares": pares, "impares": impares},
        "finais": finais
    })

@app.route('/')
def home():
    return jsonify({"status": "Backend Online", "excel": os.path.exists(EXCEL_FILE)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))