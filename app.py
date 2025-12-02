from flask import Flask, jsonify
from flask_cors import CORS
import requests
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# API oficial da Caixa — sempre funciona, rápida
CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"

def puxar_historico():
    """Puxa histórico completo da Caixa"""
    try:
        response = requests.get(CAIXA_API, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def estatisticas():
    historico = puxar_historico()
    if not historico:
        return {"erro": "Falha ao carregar histórico"}

    # Quentes/frios dos últimos 50 concursos
    ultimos_50 = historico[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['listaDezenas']:
            n = int(n)
            contagem[n] = contagem.get(n, 0) + 1

    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    frios = sorted(contagem.items(), key=lambda x: x[1])[:10]

    ultimo = historico[0]
    return {
        "ultimo_concurso": ultimo['numero'],
        "data_ultimo": ultimo['dataApuracao'],
        "ultimos_numeros": sorted([int(x) for x in ultimo['listaDezenas']]),
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(historico),
        "data_referencia": datetime.now().strftime('%d/%m/%Y %H:%M')
    }

def gerar_apostas():
    historico = puxar_historico()
    if not historico:
        return {"erro": "Falha ao carregar histórico"}

    # Fixos dos últimos 50
    ultimos_50 = historico[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['listaDezenas']:
            n = int(n)
            contagem[n] = contagem.get(n, 0) + 1

    fixos = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:4]
    fixos_nums = [n for n, c in fixos]

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
        apostas.append(criar_aposta(fixos_nums))
    for _ in range(2):
        apostas.append(criar_aposta([]))

    ultimo = historico[0]
    return {
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "ultimo_concurso": ultimo['numero'],
        "data_ultimo": ultimo['dataApuracao'],
        "fixos": fixos_nums,
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
    return jsonify({"status": "Palpiteiro V2 Backend - API Caixa Oficial", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))