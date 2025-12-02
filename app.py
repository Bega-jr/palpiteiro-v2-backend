from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

EXCEL_FILE = 'Lotofácil.xlsx'

def carregar_lotofacil():
    if not os.path.exists(EXCEL_FILE):
        print("Arquivo Lotofácil.xlsx não encontrado!")
        return []

    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        
        lotofacil = []
        for _, row in df.iterrows():
            try:
                # Extrai as 15 bolas
                numeros = []
                for i in range(1, 16):
                    col = f'Bola{i}'
                    if col in row and pd.notna(row[col]):
                        numeros.append(int(row[col]))
                
                if len(numeros) != 15:
                    continue

                concurso = int(row['Concurso'])
                data = str(row['Data Sorteio']).split(' ')[0]

                # Ganhadores e prêmios (flexível com nomes diferentes)
                def get_ganhadores(faixa):
                    colunas = [f'Ganhadores {faixa} acertos', f'Ganhadores {faixa}', f'Ganhadores_{faixa}']
                    for col in colunas:
                        if col in row and pd.notna(row[col]):
                            return int(row[col])
                    return 0

                def get_premio(faixa):
                    colunas = [f'Rateio {faixa} acertos', f'Rateio {faixa}', f'Rateio_{faixa}']
                    for col in colunas:
                        if col in row and pd.notna(row[col]):
                            return str(row[col])
                    return 'R$0,00'

                lotofacil.append({
                    'concurso': concurso,
                    'data': data,
                    'numeros': numeros,
                    'ganhadores_15': get_ganhadores(15),
                    'premio_15': get_premio(15),
                    'ganhadores_14': get_ganhadores(14),
                    'premio_14': get_premio(14),
                    'ganhadores_13': get_ganhadores(13),
                    'premio_13': get_premio(13),
                    'ganhadores_12': get_ganhadores(12),
                    'premio_12': get_premio(12),
                    'ganhadores_11': get_ganhadores(11),
                    'premio_11': get_premio(11),
                    'arrecadacao': str(row.get('Arrecadacao Total', 'R$0,00')),
                    'estimativa': str(row.get('Estimativa Prêmio', 'R$0,00')),
                    'acumulou': 'SIM' in str(row.get('Acumulado 15 acertos', ''))
                })
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                continue

        print(f"Carregados {len(lotofacil)} concursos da Lotofácil")
        return sorted(lotofacil, key=lambda x: x['concurso'], reverse=True)

    except Exception as e:
        print("Erro crítico ao ler Excel:", e)
        return []

@app.route('/api/resultados', methods=['GET'])
def resultados():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Arquivo Excel não encontrado ou corrompido"})

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
        "ganhadores": faixas,  # ← Agora sempre é array válido
        "arrecadacao": ultimo['arrecadacao'],
        "estimativa_proximo": ultimo['estimativa'],
        "acumulou": ultimo['acumulou'],
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

    apostas = []
    for i in range(7):
        base = fixos if i < 5 else []
        apostas.append(criar_aposta(base))

    ultimo = dados[0]
    return jsonify({
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "fixos": fixos,
        "apostas": apostas
    })

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - Excel Oficial Caixa", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))