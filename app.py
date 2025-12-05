from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
import random

app = Flask(__name__)
CORS(app, origins=["https://palpiteirov2.netlify.app", "*"])  # Libera tudo (Netlify + localhost)

# Caminho que funciona 100% no Vercel
EXCEL_FILE = os.path.join(os.path.dirname(__file__), 'Lotofácil.xlsx')

def carregar_lotofacil():
    print(f"Tentando carregar Excel: {EXCEL_FILE} → Existe? {os.path.exists(EXCEL_FILE)}")
    
    if not os.path.exists(EXCEL_FILE):
        print("Excel não encontrado! Usando dados de fallback...")
        return [{
            'concurso': 3552,
            'data': '05/12/2025',
            'numeros': [1,3,5,7,8,9,11,13,15,17,19,20,22,23,25],
            'ganhadores_15': 0, 'premio_15': 'R$0,00',
            'ganhadores_14': 3, 'premio_14': 'R$35.000,00',
            'ganhadores_13': 187, 'premio_13': 'R$25,00',
            'ganhadores_12': 6500, 'premio_12': 'R$10,00',
            'ganhadores_11': 78000, 'premio_11': 'R$5,00',
            'arrecadacao': 'R$28.450.000,00',
            'estimativa': 'R$6.500.000,00',
            'acumulado_15': True,
            'acumulado_especial': '',
            'observacao': ''
        }]

    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        lotofacil = []
        for _, row in df.iterrows():
            try:
                numeros = [int(row[f'Bola{i}']) for i in range(1, 16)]
                concurso = int(row['Concurso'])
                data = str(row['Data Sorteio']).split(' ')[0]
                lotofacil.append({
                    'concurso': concurso,
                    'data': data,
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
                    'acumulado_15': 'SIM' in str(row.get('Acumulado 15 acertos', '')),
                    'acumulado_especial': str(row.get('Acumulado sorteio especial Lotofácil da Independência', 'R$0,00')),
                    'observacao': str(row.get('Observação', ''))
                })
            except Exception as e:
                print(f"Erro na linha: {e}")
                continue
        return sorted(lotofacil, key=lambda x: x['concurso'], reverse=True)
    except Exception as e:
        print("Erro fatal ao ler Excel:", e)
        return []

@app.route('/api/resultados', methods=['GET'])
def resultados():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Temporariamente indisponível"}), 503
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
        "acumulou": ultimo['acumulado_15'],
        "acumulado_especial": ultimo['acumulado_especial'] if ultimo['acumulado_especial'] != 'R$0,00' else '',
        "observacao": ultimo['observacao'] if ultimo['observacao'] else '',
        "data_referencia": ultimo['data']
    })

@app.route('/api/palpites', methods=['GET'])
def palpites():
    dados = carregar_lotofacil()
    if len(dados) < 10:
        return jsonify({"erro": "Histórico insuficiente"})
    ultimos_50 = dados[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1
    fixos = [n for n, c in sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:5]]
    def criar_aposta(base=[]):
        aposta = base[:]
        candidatos = [n for n in range(1, 26) if n not in aposta]
        while len(aposta) < 15:
            escolhido = random.choice(candidatos)
            aposta.append(escolhido)
            candidatos.remove(escolhido)
        return sorted(aposta)
    apostas = [criar_aposta(fixos if i < 5 else []) for i in range(7)]
    ultimo = dados[0]
    return jsonify({
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "fixos": fixos,
        "apostas": apostas
    })

@app.route('/api/estatisticas', methods=['GET'])
def estatisticas():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Dados temporariamente indisponíveis"}), 503

    ultimos_50 = dados[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1

    mais_sorteados = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    menos_sorteados = sorted(contagem.items(), key=lambda x: x[1])[:10]
    moda = mais_sorteados[0][0] if mais_sorteados else 0

    todos_numeros = set(range(1, 26))
    sorteados_recentes = set()
    for jogo in dados[:20]:
        sorteados_recentes.update(jogo['numeros'])
    atrasados = sorted(todos_numeros - sorteados_recentes)

    somas = [sum(jogo['numeros']) for jogo in dados]
    soma_media = round(sum(somas) / len(somas)) if somas else 0

    pares_total = sum(1 for jogo in dados for n in jogo['numeros'] if n % 2 == 0)
    impares_total = sum(1 for jogo in dados for n in jogo['numeros'] if n % 2 != 0)
    media_pares = round(pares_total / len(dados))
    media_impares = round(impares_total / len(dados))

    finais = {i: 0 for i in range(10)}
    for jogo in dados:
        for n in jogo['numeros']:
            finais[n % 10] += 1

    return jsonify({
        "maisSorteados": [{"numero": n, "vezes": c} for n, c in mais_sorteados],
        "menosSorteados": [{"numero": n, "vezes": c} for n, c in menos_sorteados],
        "moda": moda,
        "atrasados": atrasados,
        "somaMedia": soma_media,
        "paresImpares": {"pares": media_pares, "impares": media_impares},
        "finais": finais
    })

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Online", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))