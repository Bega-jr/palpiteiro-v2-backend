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

# Definindo constantes para o nome do arquivo CSV e URL da fonte
CSV_FILE = 'historico_lotofacil.csv'
MAZU_URL = "www.mazusoft.com.br"

def atualizar_mazusoft():
    """Puxa o último sorteio da Mazusoft e atualiza o CSV.
       Retorna True se um novo concurso foi adicionado, False caso contrário (incluindo falhas)."""
    try:
        print(f"Tentando scraping da URL: {MAZU_URL}")
        response = requests.get(MAZU_URL, timeout=10)
        response.raise_for_status() # Lança exceção para erros HTTP
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Pega o concurso
        concurso_tag = soup.find('h2')
        if not concurso_tag:
            print("Não encontrou a tag h2 do concurso.")
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
            print(f"Encontrados {len(numeros)} números, esperado 15.")
            return False

        # Note: A data do sorteio não está sendo extraída do HTML neste código, 
        # então usamos a data atual como um placeholder.
        data_sorteio = datetime.now().strftime('%d/%m/%Y')

        novo_registro = [concurso, data_sorteio] + numeros

        # Lógica para gerenciar o arquivo CSV
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])
            ultimo_no_csv = 0
        else:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f, delimiter='\t'))
                # Assume que a primeira coluna é o concurso e a última linha é a mais recente
                ultimo_no_csv = int(reader[-1][0]) if len(reader) > 1 and reader[-1][0].isdigit() else 0

        if concurso <= ultimo_no_csv:
            print(f"Concurso {concurso} já está no CSV. Nenhuma atualização necessária.")
            return False

        # Adiciona o novo registro ao CSV
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(novo_registro)

        print(f"SUCESSO: Concurso {concurso} adicionado!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição ao tentar acessar Mazusoft: {e}")
    except Exception as e:
        print(f"Erro geral durante o scraping ou processamento: {e}")
    
    # Em caso de qualquer falha na tentativa de scraping/atualização, retorna False
    return False

def carregar_historico():
    """Carrega todos os dados do CSV para a memória."""
    if not os.path.exists(CSV_FILE):
        return []
    
    historico = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            linhas = list(reader)
            
            # Pula cabeçalho se a primeira linha não começar com um dígito
            start = 1 if linhas and not linhas[0][0].isdigit() else 0
            
            for linha in linhas[start:]:
                if len(linha) >= 17:
                    concurso = int(linha[0])
                    data = linha[1]
                    # Garante que estamos pegando exatamente 15 números
                    numeros = [int(n) for n in linha[2:17]] 
                    historico.append({
                        'concurso': concurso,
                        'data': data,
                        'numeros': numeros
                    })
    except Exception as e:
        print(f"Erro ao carregar histórico do CSV: {e}")
        return []
    
    return sorted(historico, key=lambda x: x['concurso'])

def estatisticas():
    """Calcula estatísticas dos números a partir do histórico carregado."""
    # A função carregar_historico já garante o uso do CSV local como fallback
    historico = carregar_historico()
    
    if not historico:
        return {
            "erro": "Histórico de sorteios está vazio ou não pôde ser carregado do CSV."
        }

    todos_numeros = [n for jogo in historico for n in jogo['numeros']]
    # Cria a contagem para números de 1 a 25
    contagem = {n: todos_numeros.count(n) for n in range(1, 26)}
    
    # Ordena por contagem (mais frequentes primeiro) e pega os 10 primeiros
    quentes = sorted(contagem.items(), key=lambda item: item[1], reverse=True)[:10]
    # Ordena por contagem (menos frequentes primeiro) e pega os 10 primeiros
    frios = sorted(contagem.items(), key=lambda item: item[1])[:10]

    ultimo = historico[-1]
    return {
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": ultimo['numeros'],
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(historico)
    }

def gerar_apostas():
    """Gera sugestões de apostas com base no histórico."""
    historico = carregar_historico()
    
    if len(historico) < 10:
        # Gera aleatório se histórico pequeno
        apostas = []
        for _ in range(7):
            aposta = sorted(random.sample(range(1, 26), 15))
            apostas.append(aposta)
        return {
            "gerado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "fixos": [],
            "apostas": apostas,
            "aviso": "Historico pequeno, gerando apostas aleatórias."
        }

    # Lógica de fixos dos últimos 50 sorteios (seu código original)
    ultimos_50 = historico[-50:]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1
    # Pega os 4 mais frequentes nos últimos 50 jogos
    fixos = sorted(contagem.items(), key=lambda item: item[1], reverse=True)[:4]
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
    # 5 apostas com os fixos, 2 aleatórias
    for _ in range(5):
        apostas.append(criar_aposta(fixos_nums))
    for _ in range(2):
        apostas.append(criar_aposta([]))

    return {
        "gerado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "fixos": fixos_nums,
        "apostas": apostas
    }

# --- Rotas da API ---

@app.route('/api/atualizar', methods=['GET'])
def atualizar_endpoint():
    """Endpoint manual para forçar a atualização e verificar o status."""
    sucesso = atualizar_mazusoft()
    return jsonify({"atualizado_com_novo_concurso": sucesso, "fonte": "Mazusoft/CSV"})

@app.route('/api/palpites', methods=['GET'])
def palpites_endpoint():
    """Tenta atualizar e gera palpites com base nos dados mais recentes (online ou CSV)."""
    atualizar_mazusoft() # Tenta atualizar (se falhar, apenas continua)
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados_endpoint():
    """Tenta atualizar e retorna estatísticas com base nos dados mais recentes (online ou CSV)."""
    atualizar_mazusoft() # Tenta atualizar (se falhar, apenas continua)
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Mazusoft Auto-Update", "online": True, "endpoints_disponiveis": ["/api/atualizar", "/api/palpites", "/api/resultados"]})

if __name__ == '__main__':
    # Cria o arquivo CSV vazio se ele não existir na inicialização, garantindo que o app não quebre na primeira leitura.
    if not os.path.exists(CSV_FILE):
        print(f"Arquivo {CSV_FILE} não encontrado, criando arquivo vazio com cabeçalho.")
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])

    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
