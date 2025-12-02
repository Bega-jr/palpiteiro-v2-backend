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
    """Lê direto o Excel oficial da Caixa (Lotofácil.xlsx)"""
    if not os.path.exists(EXCEL_FILE):
        print("Arquivo Lotofácil.xlsx não encontrado!")
        return []

    try:
        # Lê o Excel (engine openpyxl é obrigatório pro .xlsx)
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        
        lotofacil = []
        for _, row in df.iterrows():
            try:
                # Extrai as 15 bolas (colunas Bola1 até Bola15)
                numeros = []
                for i in range(1, 16):
                    bola_col = f'Bola{i}'
                    if bola_col in row and pd.notna(row[bola_col]):
                        numeros.append(int(row[bola_col]))
                
                if len(numeros) == 15:
                    concurso = int(row['Concurso'])
                    data = str(row['Data Sorteio']).split(' ')[0]  # Remove hora se tiver
                    
                    lotofacil.append({
                        'concurso': concurso,
                        'data': data,
                        'numeros': numeros,  # Ordem oficial de sorteio
                        'ganhadores_15': int(row['Ganhadores 15 acertos']) if 'Ganhadores 15 acertos' in row and pd.notna(row['Ganhadores 15 acertos']) else 0,
                        'premio_15': str(row.get('Rateio 15 acertos', 'R$0,00')),
                        'ganhadores_14': int(row['Ganhadores 14 acertos']) if 'Ganhadores 14 acertos' in row else 0,
                        'premio_14': str(row.get('Rateio 14 acertos', 'R$0,00')),
                        'ganhadores_13': int(row['Ganhadores 13 acertos']) if 'Ganhadores 13 acertos' in row else 0,
                        'premio_13': str(row.get('Rateio 13 acertos', 'R$0,00')),
                        'ganhadores_12': int(row['Ganhadores 12 acertos']) if 'Ganhadores 12 acertos' in row else 0,
                        'premio_12': str(row.get('Rateio 12 acertos', 'R$0,00')),
                        'ganhadores_11': int(row['Ganhadores 11 acertos']) if 'Ganhadores 11 acertos' in row else 0,
                        'premio_11': str(row.get('Rateio 11 acertos', 'R$0,00')),
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

def estatisticas():
    dados = carregar_lotofacil()
    if not dados:
        return {"erro": "Não foi possível carregar o histórico"}

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
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(dados),
        "data_referencia": ultimo['data']
    }

def gerar_apostas():
    dados = carregar_lotofacil()
    if len(dados) < 10:
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
    estrategias = ['Quentes + Fixos', 'Frios + Balanceado', 'Equilíbrio Total', 'Final 0', 'Padrão Caixa', 'Modo Grok', 'Surpresa Máxima']
    for i in range(7):
        base = fixos if i < 5 else []
        apostas.append({
            "id": i + 1,
            "estrategia": estrategias[i],
            "numbers": criar_aposta(base),
            "fixos_usados": base
        })

    ultimo = dados[0]
    return {
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "fixos": fixos,
        "apostas": [a["numbers"] for a in apostas],
        "estrategias": [a["estrategia"] for a in apostas]
    }

@app.route('/api/palpites', methods=['GET'])
def palpites():
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Arquivo Excel não encontrado"})
    
    ultimo = dados[0]
    faixas = [
        {"faixa": "15 acertos", "ganhadores": ultimo.get('ganhadores_15', 0), "premio": ultimo.get('premio_15', 'R$0,00')},
        {"faixa": "14 acertos", "ganhadores": ultimo.get('ganhadores_14', 0), "premio": ultimo.get('premio_14', 'R$0,00')},
        {"faixa": "13 acertos", "ganhadores": ultimo.get('ganhadores_13', 0), "premio": ultimo.get('premio_13', 'R$0,00')},
        {"faixa": "12 acertos", "ganhadores": ultimo.get('ganhadores_12', 0), "premio": ultimo.get('premio_12', 'R$0,00')},
        {"faixa": "11 acertos", "ganhadores": ultimo.get('ganhadores_11', 0), "premio": ultimo.get('premio_11', 'R$0,00')},
    ]

    return jsonify({
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": ultimo['numeros'],
        "ganhadores": faixas,
        "arrecadacao": ultimo.get('arrecadacao', 'R$0,00'),
        "estimativa_proximo": ultimo.get('estimativa', 'R$0,00'),
        "acumulou": ultimo.get('acumulou', False),
        "data_referencia": ultimo['data']
    })

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - Excel Oficial Caixa", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))