from flask import Flask, jsonify
from flask_cors import CORS
import requests
import csv
import os
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

CSV_FILE = 'historico_lotofacil.csv'
CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"

def puxar_ultimo_concurso():
    """Puxa o último concurso da API oficial da Caixa"""
    try:
        response = requests.get(CAIXA_API, timeout=10)
        if response.status_code != 200:
            print("Erro na API Caixa:", response.status_code)
            return None
        
        data = response.json()
        concurso = data['numero']
        dezenas = sorted([int(x) for x in data['listaDezenas']])
        data_str = data['dataApuracao']  # dd/mm/yyyy
        data_formatada = datetime.strptime(data_str, '%d/%m/%Y').strftime('%d/%m/%Y')
        
        return {
            'concurso': concurso,
            'data': data_formatada,
            'numeros': dezenas
        }
    except Exception as e:
        print("Erro ao puxar último concurso:", e)
        return None

def atualizar_historico():
    """Atualiza o CSV com o último concurso da Caixa"""
    try:
        ultimo = puxar_ultimo_concurso()
        if not ultimo:
            return False

        print(f"Último concurso da Caixa: {ultimo['concurso']}")

        # Cria CSV se não existir
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])
            ultimo_no_csv = 0
        else:
            # Lê o último concurso do CSV
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                ultimo_no_csv = int(reader[-1][0]) if len(reader) > 1 else 0

        print(f"Último no CSV: {ultimo_no_csv}")

        if ultimo['concurso'] <= ultimo_no_csv:
            print("Já está atualizado!")
            return False

        # Adiciona o novo concurso
        registro = [ultimo['concurso'], ultimo['data']] + ultimo['numeros']
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(registro)

        print(f"Concurso {ultimo['concurso']} adicionado com sucesso!")
        return True

    except Exception as e:
        print("Erro no update:", e)
        return False

def carregar_historico():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def estatisticas():
    historico = carregar_historico()
    if not historico:
        return {"erro": "Histórico vazio"}

    todos_numeros = []
    for row in historico:
        nums = [int(row[f'n{i}']) for i in range(1,16)]
        todos_numeros.extend(nums)

    contagem = {n: todos_numeros.count(n) for n in range(1, 26)}
    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    frios = sorted(contagem.items(), key=lambda x: x[1])[:10]

    ultimo = historico[-1]
    return {
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": [int(ultimo[f'n{i}']) for i in range(1,16)],
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(historico)
    }

def gerar_apostas():
    historico = carregar_historico()
    if len(historico) < 10:
        return {"erro": "Histórico insuficiente"}

    ultimos_50 = historico[-50:]
    contagem = {}
    for row in ultimos_50:
        for i in range(1,16):
            n = int(row[f'n{i}'])
            contagem[n] = contagem.get(n, 0) + 1
    fixos = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:4]
    fixos_nums = [n for n, c in fixos]

    def criar_aposta(base=[]):
        aposta = base[:]
        candidatos = [n for n in range(1,26) if n not in aposta]
        while len(aposta) < 15:
            escolhido = random.choice(candidatos)
            aposta.append(escolhido)
            candidatos.remove(escolhido)
        return sorted(aposta)

    apostas = []
    for _ in range(5):
        apostas.append(criar_aposta(fixos_nums))
    for _ in range(2):
        apostas.append(criar_aposta([]))

    return {
        "gerado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "fixos": fixos_nums,
        "apostas": apostas
    }

@app.route('/api/atualizar', methods=['GET'])
def atualizar():
    sucesso = atualizar_historico()
    return jsonify({"atualizado": sucesso, "fonte": "API Oficial Caixa"})

@app.route('/api/palpites', methods=['GET'])
def palpites():
    atualizar_historico()
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    atualizar_historico()
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - Backend com API Caixa Oficial", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))