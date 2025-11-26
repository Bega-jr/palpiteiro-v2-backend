from flask import Flask, jsonify
from flask_cors import CORS
import requests
import csv
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

CSV_FILE = 'historico_lotofacil.csv'
CAIXA_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"

def puxar_concurso(concurso: int):
    """Puxa um concurso específico da API da Caixa"""
    url = f"{CAIXA_BASE}/{concurso}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'listaDezenas' in data:
                dezenas = sorted(data['listaDezenas'])
                data_sorteio = data['dataApuracao']  # dd/mm/yyyy
                data_formatada = datetime.strptime(data_sorteio, '%d/%m/%Y').strftime('%d/%m/%Y')
                return [concurso, data_formatada] + dezenas
    except:
        pass
    return None

def atualizar_historico_completo():
    """Atualiza do último no CSV até o mais recente da Caixa"""
    try:
        # Puxa o último da Caixa
        ultimo_url = f"{CAIXA_BASE}/{0}"  # 0 = último
        response = requests.get(ultimo_url, timeout=10)
        if response.status_code != 200:
            return False
        
        ultimo_concurso = response.json()['numero']
        print(f"Último concurso na Caixa: {ultimo_concurso}")

        if not os.path.exists(CSV_FILE):
            # Cria CSV vazio
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])
            ultimo_no_csv = 0
        else:
            # Lê último do CSV
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                linhas = list(reader)
                ultimo_no_csv = int(linhas[-1][0]) if linhas[1:] else 0

        print(f"Último no CSV: {ultimo_no_csv}")

        if ultimo_concurso <= ultimo_no_csv:
            print("Já está atualizado!")
            return True

        # Preenche o gap
        novos_registros = []
        for concurso in range(ultimo_no_csv + 1, ultimo_concurso + 1):
            registro = puxar_concurso(concurso)
            if registro:
                novos_registros.append(registro)
                print(f"Adicionado concurso {concurso}")
            else:
                print(f"Falhou concurso {concurso}")

        if novos_registros:
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(novos_registros)
            print(f"Adicionados {len(novos_registros)} concursos novos!")
            return True

    except Exception as e:
        print(f"Erro no auto-update: {e}")
        return False

# Suas funções de gerar_apostas e estatisticas (igual antes)
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

    # Fixos dos últimos 50
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

# Rotas
@app.route('/api/atualizar', methods=['GET'])
def atualizar():
    sucesso = atualizar_historico_completo()
    return jsonify({"atualizado": sucesso, "fonte": "Caixa API"})

@app.route('/api/palpites', methods=['GET'])
def palpites():
    atualizar_historico_completo()
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    atualizar_historico_completo()
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Auto-Update Caixa", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))