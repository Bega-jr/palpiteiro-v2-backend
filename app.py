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
    """Lê direto o arquivo .xlsx oficial da Caixa"""
    if not os.path.exists(EXCEL_FILE):
        return None
    
    try:
        # Lê o Excel (pula linhas vazias)
        df = pd.read_excel(EXCEL_FILE, sheet_name=0, engine='openpyxl')
        
        # Converte pra lista de dicts
        dados = df.to_dict('records')
        
        lotofacil = []
        for row in dados:
            try:
                # Extrai as 15 bolas (colunas Bola1 a Bola15)
                numeros = []
                for i in range(1, 16):
                    bola = row.get(f'Bola{i}') or row.get(f'Bola {i}')
                    if pd.notna(bola):
                        numeros.append(int(bola))
                
                if len(numeros) == 15:
                    lotofacil.append({
                        'concurso': int(row['Concurso']),
                        'data': str(row['Data Sorteio']).split(' ')[0],  # Formato dd/mm/aaaa
                        'numeros': numeros,  # Ordem oficial de sorteio
                        'ganhadores_15': int(row['Ganhadores 15 acertos']) if pd.notna(row.get('Ganhadores 15 acertos')) else 0,
                        'premio_15': str(row.get('Rateio 15 acertos', 'R$0,00'))
                    })
            except:
                continue
                
        return sorted(lotofacil, key=lambda x: x['concurso'], reverse=True)
        
    except Exception as e:
        print("Erro ao ler Excel:", e)
        return None

def estatisticas():
    dados = carregar_lotofacil()
    if not dados:
        return {"erro": "Arquivo Lotofácil.xlsx não encontrado ou corrompido"}

    ultimos_50 = dados[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1

    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    frios = sorted(contagem.items(), key=lambda x: x[1])[:10]

    ultimo = dados[0]
    return {
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": ultimo['numeros'],
        "ganhadores_15": ultimo['ganhadores_15'],
        "premio_15": ultimo['premio_15'],
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(dados),
        "data_referencia": datetime.now().strftime('%d/%m/%Y %H:%M')
    }

def gerar_apostas():
    dados = carregar_lotofacil()
    if not dados or len(dados) < 10:
        return {"erro": "Histórico insuficiente"}

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
    for _ in range(5):
        apostas.append(criar_aposta(fixos))
    for _ in range(2):
        apostas.append(criar_aposta([]))

    ultimo = dados[0]
    return {
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "fixos": fixos,
        "apostas": apostas
    }

@app.route('/api/palpites', methods=['GET'])
def palpites():
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - Excel Oficial Caixa", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))