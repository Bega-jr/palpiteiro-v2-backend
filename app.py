from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

CSV_FILE = 'historico_lotofacil.csv'
MAZU_URL = "https://www.mazusoft.com.br/lotofacil/resultado.php"

def atualizar_mazusoft():
    """Puxa o último sorteio da Mazusfot e atualiza o CSV"""
    try:
        response = requests.get(MAZU_URL, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Pega o concurso
        concurso_tag = soup.find('h2')
        if not concurso_tag:
            return False
        concurso = int(''.join(filter(str.isdigit, concurso_tag.text)))

        # Pega os números na ordem de sorteio
        bolas = soup.find_all('div', class_='bola')
        numeros = []
        for b in bolas:
            num = b.text.strip()
            if num.isdigit() and len(num) <= 2:
                numeros.append(int(num))
        
        if len(numeros) != 15:
            return False

        data_sorteio = datetime.now().strftime('%d/%m/%Y')  # Usa data atual se não achar no HTML

        novo_registro = [concurso, data_sorteio] + numeros  # Ordem de sorteio oficial

        # Cria CSV se não existir
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='\t')  # Tabulação como o seu
                writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])
            ultimo_no_csv = 0
        else:
            # Lê último do CSV
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f, delimiter='\t'))
                ultimo_no_csv = int(reader[-1][0]) if len(reader) > 1 else 0

        if concurso <= ultimo_no_csv:
            return False

        # Adiciona o novo
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(novo_registro)

        print(f"Concurso {concurso} adicionado com sucesso!")
        return True

    except Exception as e:
        print("Erro ao atualizar Mazusoft:", e)
        return False

def carregar_historico():
    if not os.path.exists(CSV_FILE):
        return []
    
    historico = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        linhas = list(reader)
        
        # Pula cabeçalho se existir
        start = 1 if linhas and not linhas[0][0].isdigit() else 0
        
        for linha in linhas[start:]:
            if len(linha) >= 17:
                try:
                    concurso = int(linha[0])
                    data = linha[1]
                    numeros = [int(linha[i]) for i in range(2, 17)]
                    historico.append({
                        'concurso': concurso,
                        'data': data,
                        'numeros': numeros
                    })
                except ValueError:
                    continue
    
    return sorted(historico, key=lambda x: x['concurso'])

def estatisticas():
    historico = carregar_historico()
    if not historico:
        # Retorna JSON de erro aqui, que é tratado corretamente no frontend
        return {
            "erro": "Histórico de sorteios está vazio ou não pôde ser carregado."
        }

    todos_numeros = [n for jogo in historico for n in jogo['numeros']]
    contagem = {n: todos_numeros.count(n) for n in range(1, 26)}
    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    frios = sorted(contagem.items(), key=lambda x: x[1])[:10]

    ultimo = historico[-1]
    return {
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": ultimo['numeros'],  # Ordem de sorteio
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(historico)
    }

def gerar_apostas():
    historico = carregar_historico()
    if "erro" in historicas_stats: # Verifica se a estatistica retornou erro
         return historicas_stats

    if len(historico) < 10:
        # Gera aleatório se histórico pequeno
        apostas = []
        for _ in range(7):
            aposta = sorted(random.sample(range(1, 26), 15))
            apostas.append(aposta)
        return {
            "gerado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "fixos": [],
            "apostas": apostas
        }

    # Fixos dos últimos 50
    ultimos_50 = historico[-50:]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem = contagem.get(n, 0) + 1
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
    sucesso = atualizar_mazusoft()
    return jsonify({"atualizado": sucesso, "fonte": "Mazusoft"})

@app.route('/api/palpites', methods=['GET'])
def palpites():
    atualizar_mazusoft()
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    atualizar_mazusoft()
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Mazusfot Auto-Update", "online": True})

# NOVO: Tratador de erro 404 (Not Found)
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error="O endpoint requisitado não foi encontrado nesta URL. Verifique a documentação da API."), 404

# NOVO: Tratador de erro 500 (Internal Server Error)
@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error="Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde."), 500

if __name__ == '__main__':
    # Use 0.0.0.0 para que o Render consiga ligar o servidor, e use a porta de ambiente
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
