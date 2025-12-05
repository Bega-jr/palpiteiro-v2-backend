from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
import random

app = Flask(__name__)

# CORS CONFIGURADO PRA FUNCIONAR COM NETLIFY
CORS(app, origins=["https://palpiteirov2.netlify.app", "http://localhost:3000"])

# CAMINHO QUE FUNCIONA NO VERCEL (RAIZ DO PROJETO)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'Lotofácil.xlsx')

def carregar_lotofacil():
    print(f"Tentando carregar Excel de: {EXCEL_PATH}")
    print(f"Arquivo existe? {os.path.exists(EXCEL_PATH)}")
    
    if not os.path.exists(EXCEL_PATH):
        print("Excel não encontrado! Usando dados de fallback...")
        # Dados de fallback pra não quebrar o site
        return [{
            'concurso': 3551,
            'data': '04/12/2025',
            'numeros': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
            'ganhadores_15': 0,
            'premio_15': 'R$0,00',
            'ganhadores_14': 5,
            'premio_14': 'R$25.000,00',
            'ganhadores_13': 150,
            'premio_13': 'R$25,00',
            'ganhadores_12': 5000,
            'premio_12': 'R$10,00',
            'ganhadores_11': 50000,
            'premio_11': 'R$5,00',
            'arrecadacao': 'R$21.696.328,50',
            'estimativa': 'R$5.000.000,00',
            'acumulado_15': True,
            'acumulado_especial': '',
            'observacao': ''
        }]

    try:
        df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
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
                print(f"Erro ao processar linha: {e}")
                continue

        print(f"Carregados {len(lotofacil)} concursos da Lotofácil")
        return sorted(lotofacil, key=lambda x: x['concurso'], reverse=True)

    except Exception as e:
        print("Erro ao ler Excel:", e)
        return []

@app.route('/api/resultados', methods=['GET'])
def resultados():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Erro interno do servidor"}), 500

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

# Mantém os outros endpoints (palpites, estatisticas, etc) iguais...
# (só copia os que você já tem)

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - Backend Online", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))