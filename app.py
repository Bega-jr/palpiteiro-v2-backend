from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app, origins=["https://palpiteirov2.netlify.app", "*"])

# ARQUIVO NA RAIZ DO PROJETO — SÓ FUNCIONA SE O EXCEL ESTIVER LÁ
EXCEL_FILE = "Lotofácil.xlsx"

def carregar_lotofacil():
    print(f"Procurando Excel em: {EXCEL_FILE}")
    
    if not os.path.exists(EXCEL_FILE):
        print("ERRO: Arquivo Lotofácil.xlsx não encontrado!")
        return None

    try:
        print("Lendo Excel com pandas...")
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        print(f"Excel carregado com sucesso! {len(df)} concursos encontrados.")

        dados = []
        for _, row in df.iterrows():
            try:
                numeros = [int(row[f'Bola{i}']) for i in range(1, 16)]
                concurso = int(row['Concurso'])
                data = str(row['Data Sorteio']).split(' ')[0]

                dados.append({
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
                    'acumulado_15': 'SIM' in str(row.get('Acumulado 15 acertos', ''))
                })
            except Exception as e:
                print(f"Erro ao processar linha do concurso {row.get('Concurso', 'desconhecido')}: {e}")
                continue

        return sorted(dados, key=lambda x: x['concurso'], reverse=True)

    except Exception as e:
        print("ERRO FATAL ao ler o Excel:", e)
        return None

@app.route('/api/resultados')
def resultados():
    dados = carregar_lotofacil()
    
    if not dados:
        return jsonify({
            "erro": "Arquivo Lotofácil.xlsx não encontrado ou corrompido",
            "status": "Por favor, atualize o arquivo no repositório"
        }), 500

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

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Online", "excel": os.path.exists(EXCEL_FILE)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))