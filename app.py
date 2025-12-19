from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Libera pro frontend acessar

EXCEL_FILE = "Lotofácil.xlsx"  # Arquivo na raiz do repositório

def carregar_lotofacil():
    if not os.path.exists(EXCEL_FILE):
        print("Arquivo Lotofácil.xlsx não encontrado!")
        return None

    try:
        print("Carregando o Excel oficial da Caixa...")
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
                    'arrecadacao': str(row.get('Arrecadacao Total', 'R$0,00')),
                    'estimativa': str(row.get('Estimativa Prêmio', 'R$0,00')),
                    'acumulado_15': 'SIM' in str(row.get('Acumulado 15 acertos', ''))
                })
            except Exception as e:
                print(f"Linha ignorada: {e}")
                continue

        print(f"Carregados {len(dados)} concursos com sucesso!")
        return sorted(dados, key=lambda x: x['concurso'], reverse=True)

    except Exception as e:
        print("Erro ao ler o Excel:", e)
        return None

@app.route('/api/resultados')
def resultados():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Arquivo Lotofácil.xlsx não encontrado"}), 500

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
        "atrasados": atrasados,
        "somaMedia": soma_media,
        "paresImpares": {"pares": pares, "impares": impares},
        "finais": finais
    })

@app.route('/api/palpites-vip')
def palpites_vip():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Dados indisponíveis"}), 503

    ultimos_50 = dados[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1

    quentes = [n for n, c in sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:8]]

    def gerar():
        aposta = quentes[:random.randint(5, 7)]
        while len(aposta) < 15:
            n = random.randint(1, 25)
            if n not in aposta:
                aposta.append(n)
        return sorted(aposta)

    return jsonify({
        "quentes": quentes,
        "apostas": [gerar() for _ in range(7)],
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M')
    })

@app.route('/')
def home():
    return jsonify({
        "status": "Palpiteiro V2 Backend - Online",
        "excel_ok": os.path.exists(EXCEL_FILE)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
