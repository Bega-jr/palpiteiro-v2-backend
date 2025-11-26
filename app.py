# app.py — Palpiteiro V2 Backend (evolução da V1)
from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)  # Permite o frontend do Netlify

CSV_FILE = 'historico_lotofacil.csv'
MAZU_URL = "https://www.mazusoft.com.br/lotofacil/resultado.php"

# ========================
# 1. Atualiza CSV automaticamente
# ========================
def atualizar_historico():
    try:
        response = requests.get(MAZU_URL, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        concurso_tag = soup.find('h2')
        if not concurso_tag:
            return False
        concurso = int(''.join(filter(str.isdigit, concurso_tag.text)))

        bolas = soup.find_all('div', class_='bola')
        numeros = sorted([int(b.text.strip()) for b in bolas if b.text.strip().isdigit()][:15])
        
        if len(numeros) != 15:
            return False

        novo_registro = [concurso, datetime.now().strftime('%d/%m/%Y')] + numeros

        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])
                writer.writerow(novo_registro)
            return True

        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            linhas = list(reader)
            concursos = [int(row[0]) for row in linhas[1:] if row and row[0].isdigit()]

        if concurso not in concursos:
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(novo_registro)
            return True
    except Exception as e:
        print("Erro ao atualizar histórico:", e)
    return False

# ========================
# 2. Carrega histórico
# ========================
def carregar_historico():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

# ========================
# 3. Calcula estatísticas
# ========================
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

# ========================
# 4. Gera apostas (fixos + modo Grok)
# ========================
def gerar_apostas():
    historico = carregar_historico()
    if len(historico) < 10:
        return {"erro": "Histórico insuficiente"}

    # Fixos: 4 números mais sorteados nos últimos 50
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
        apostas.append(criar_aposta())

    return {
        "gerado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "fixos": fixos_nums,
        "apostas": apostas
    }

# ========================
# ROTAS
# ========================
@app.route('/api/atualizar', methods=['GET'])
def atualizar():
    atualizado = atualizar_historico()
    return jsonify({"atualizado": atualizado})

@app.route('/api/palpites', methods=['GET'])
def palpites():
    atualizar_historico()
    dados = gerar_apostas()
    return jsonify(dados)

@app.route('/api/resultados', methods=['GET'])
def resultados():
    atualizar_historico()
    dados = estatisticas()
    return jsonify(dados)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Palpiteiro V2 Backend rodando!", "versao": "2.0"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))