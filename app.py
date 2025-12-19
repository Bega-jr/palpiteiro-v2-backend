from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

TXT_FILE = 'Lotofácil.txt'
LAST_UPDATE_FILE = 'last_update.txt'
CAIXA_LOTOFACIL_URL = "https://loterias.caixa.gov.br/wps/wcm/connect/loterias-caixa/landing-lotofacil/lotofacil-historico"
# API oficial da Caixa — sempre funciona, rápida
CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"

def baixar_historico_oficial():
    """Baixa o TXT oficial da Caixa para Lotofácil"""
    try:
        print("Baixando histórico oficial da Caixa...")
        response = requests.get(CAIXA_LOTOFACIL_URL, timeout=30, allow_redirects=True)
        response.raise_for_status()
        with open(TXT_FILE, 'wb') as f:
            f.write(response.content)
        print("Arquivo oficial baixado e salvo!")
        return True
    except Exception as e:
        print("Erro ao baixar histórico:", e)
        return False

def carregar_historico():
    """Lê o TXT oficial e retorna lista de concursos"""
    if not os.path.exists(TXT_FILE):
        return []

    historico = []
def puxar_historico():
    """Puxa histórico completo da Caixa"""
    try:
        with open(TXT_FILE, 'r', encoding='latin1') as f:  # Encoding da Caixa
            for linha in f:
                linha = linha.strip()
                if linha.startswith('Lotofácil'):
                    partes = linha.split('\t')
                    if len(partes) >= 20:  # Suficiente para concurso, data, 15 dezenas
                        try:
                            concurso = int(partes[1])
                            data = partes[2]
                            numeros = [int(partes[i]) for i in range(5, 20)]  # 15 dezenas na ordem de sorteio
                            ganhadores = int(partes[20]) if partes[20].isdigit() else 0  # Ganhadores 15 acertos
                            premio = float(partes[21].replace(',', '.')) if partes[21] else 0.0  # Prêmio 15 acertos
                            arrecadacao = float(partes[22].replace(',', '.')) if partes[22] else 0.0  # Arrecadação
                            historico.append({
                                'concurso': concurso,
                                'data': data,
                                'numeros': numeros,
                                'ganhadores_15': ganhadores,
                                'premio_15': premio,
                                'arrecadacao': arrecadacao
                            })
                        except (ValueError, IndexError):
                            continue
    except Exception as e:
        print("Erro ao ler TXT:", e)

    return sorted(historico, key=lambda x: x['concurso'])

def atualizar_se_necessario():
    """Verifica e atualiza o arquivo se necessário"""
    try:
        ultima_atualizacao = None
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                ultima_atualizacao = f.read().strip()

        hoje = datetime.now().strftime('%Y-%m-%d')
        if ultima_atualizacao == hoje:
            return True

        # Verifica último concurso oficial (API rápida)
        response = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest", timeout=10)
        ultimo_oficial = response.json()['concurso'] if response.status_code == 200 else None

        if ultimo_oficial:
            dados = carregar_historico()
            ultimo_local = dados[-1]['concurso'] if dados else 0
            if ultimo_oficial > ultimo_local:
                print(f"Novo concurso! {ultimo_local} → {ultimo_oficial}")
                if baixar_historico_oficial():
                    with open(LAST_UPDATE_FILE, 'w') as f:
                        f.write(hoje)
                    return True
    except Exception as e:
        print("Erro no update:", e)
    return False

@app.route('/api/atualizar', methods=['GET'])
def forcar_atualizacao():
    baixar_historico_oficial()
    return jsonify({"status": "Histórico oficial atualizado!"})
        response = requests.get(CAIXA_API, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@app.route('/api/resultados', methods=['GET'])
def resultados():
    atualizar_se_necessario()
    historico = carregar_historico()
def estatisticas():
    historico = puxar_historico()
    if not historico:
        return jsonify({"erro": "Histórico vazio"})
    
    ultimo = historico[-1]
    # Ganhadores e premiação por faixa (simplificado; expanda com mais colunas do TXT se precisar)
    ganhadores = [0, 0, 0, 0, 0]  # 11-15 acertos (expanda com dados do TXT)
    premiacao = [0.0, 0.0, 0.0, 0.0, 0.0]  # Valores por faixa

    return jsonify({
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "numeros_sorteados": ultimo['numeros'],  # Ordem de sorteio
        "ganhadores_por_faixa": ganhadores,  # 11,12,13,14,15
        "premiacao_por_faixa": premiacao,  # Valores por faixa
        "arrecadacao": ultimo['arrecadacao'],
        "data_referencia": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "total_sorteios": len(historico)
    })
        return {"erro": "Falha ao carregar histórico"}

@app.route('/api/palpites', methods=['GET'])
def palpites():
    atualizar_se_necessario()
    historico = carregar_historico()
    if len(historico) < 10:
        return jsonify({"erro": "Histórico insuficiente para estatísticas"})
    # Quentes/frios dos últimos 50 concursos
    ultimos_50 = historico[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['listaDezenas']:
            n = int(n)
            contagem[n] = contagem.get(n, 0) + 1

    # Fixos dos últimos 50 (mais sorteados, pra acertos 11-15)
    ultimos_50 = historico[-50:]
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
        for n in jogo['numeros']:
        for n in jogo['listaDezenas']:
            n = int(n)
            contagem[n] = contagem.get(n, 0) + 1
    fixos = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:5]  # 5 fixos pra desdobramentos

    fixos = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:4]
    fixos_nums = [n for n, c in fixos]

    # Gera 7 desdobramentos baseados em fixos (otimizado pra 11-15 acertos)
    def criar_desdobramento(base=[]):
    def criar_aposta(base=[]):
        aposta = base[:]
        candidatos = [n for n in range(1,26) if n not in aposta]
        # Peso maior pros números "quentes" (mais sorteados)
        pesos = [contagem.get(n, 1) for n in candidatos]
        candidatos = [n for n in range(1, 26) if n not in aposta]
        while len(aposta) < 15:
            escolhido = random.choices(candidatos, weights=pesos)[0]
            escolhido = random.choice(candidatos)
            aposta.append(escolhido)
            candidatos.remove(escolhido)
            pesos.pop(candidatos.index(escolhido))  # Ajusta pesos
        return sorted(aposta)

    desdobramentos = []
    for _ in range(7):
        desdobramento = criar_desdobramento(fixos_nums)
        desdobramentos.append({
            "numbers": desdobramento,
            "fixos": fixos_nums,
            "stats": {
                "sum": sum(desdobramento),
                "even": len([n for n in desdobramento if n % 2 == 0]),
                "odd": len([n for n in desdobramento if n % 2 != 0])
            }
        })

    return jsonify({
    apostas = []
    for _ in range(5):
        apostas.append(criar_aposta(fixos_nums))
    for _ in range(2):
        apostas.append(criar_aposta([]))

    ultimo = historico[0]
    return {
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "data_referencia": datetime.now().strftime('%d/%m/%Y'),
        "ultimo_concurso": ultimo['numero'],
        "data_ultimo": ultimo['dataApuracao'],
        "fixos": fixos_nums,
        "desdobramentos": desdobramentos
    })
        "apostas": apostas
    }

@app.route('/api/estatisticas', methods=['GET'])
def estatisticas():
    atualizar_se_necessario()
    historico = carregar_historico()
    if not historico:
        return jsonify({"erro": "Histórico vazio"})

    todos_numeros = [n for jogo in historico for n in jogo['numeros']]
    contagem = {n: todos_numeros.count(n) for n in range(1, 26)}
    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    frios = sorted(contagem.items(), key=lambda x: x[1])[:10]
@app.route('/api/palpites', methods=['GET'])
def palpites():
    return jsonify(gerar_apostas())

    return jsonify({
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(historico),
        "data_referencia": datetime.now().strftime('%d/%m/%Y')
    })
@app.route('/api/resultados', methods=['GET'])
def resultados():
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Backend Lotofácil - Dados Oficiais Caixa", "versao": "1.0"})
    return jsonify({"status": "Palpiteiro V2 Backend - API Caixa Oficial", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
