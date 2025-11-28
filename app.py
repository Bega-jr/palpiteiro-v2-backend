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
MAZU_URL = "www.mazusoft.com.br"

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
                # Lida melhor com leitura do último concurso, assume que é o primeiro campo numérico da última linha
                try:
                    ultimo_no_csv = int(reader[-1][0]) if len(reader) > 1 else 0
                except (ValueError, IndexError):
                    ultimo_no_csv = 0

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
        # Verifica se a primeira linha parece ser um cabeçalho não numérico
        start = 1 if linhas and not linhas[0][0].isdigit() else 0
        
        for linha in linhas[start:]:
            if len(linha) >= 17:
                try:
                    concurso = int(linha[0])
                    data = linha[1]
                    # Ajustado para carregar corretamente a partir da terceira coluna (índice 2)
                    numeros = [int(linha[i]) for i in range(2, 17)] 
                    historico.append({
                        'concurso': concurso,
                        'data': data,
                        'numeros': numeros
                    })
                except (ValueError, IndexError):
                    continue
    
    # Ordena por concurso do mais antigo para o mais novo
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
    # Ordenação por contagem
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

# Função auxiliar para verificar a paridade
def check_paridade(aposta):
    pares = sum(1 for n in aposta if n % 2 == 0)
    impares = sum(1 for n in aposta if n % 2 != 0)
    # Aceita 7/8 ou 8/7
    return (pares == 7 and impares == 8) or (pares == 8 and impares == 7)


def gerar_apostas():
    historico = carregar_historico()
    
    # CORREÇÃO: Verifica se o histórico está vazio e retorna erro JSON tratável
    if not historico or "erro" in estatisticas(): 
         return {
            "erro": "Histórico vazio. Impossível gerar palpites estatísticos."
         }

    # Restante da lógica (histórico pequeno/grande)
    if len(historico) < 10:
        apostas = []
        for _ in range(7):
            # Garante que até apostas aleatórias sigam a paridade
            aposta = []
            while not check_paridade(aposta):
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
        # Gerador ajustado para forçar a verificação de paridade
        aposta = []
        while not check_paridade(aposta):
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
    return jsonify({"atualizado": sucesso, "fonte": "Mazusfot"})

@app.route('/api/palpites', methods=['GET'])
def palpites():
    atualizar_mazusoft()
    # A função gerar_apostas agora retorna um JSON tratável, mesmo se houver erro
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    atualizar_mazusoft()
    # A função estatisticas agora retorna um JSON tratável, mesmo se houver erro
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Mazusoft Auto-Update", "online": True})

# Tratador de erro 404 (Not Found)
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error="O endpoint requisitado não foi encontrado nesta URL. Verifique a documentação da API."), 404

# Tratador de erro 500 (Internal Server Error)
@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error="Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde."), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
