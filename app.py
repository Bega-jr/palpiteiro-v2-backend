from flask import Flask, jsonify
from flask_cors import CORS
import requests
import csv
import os
from datetime import datetime
import random
import zipfile
from io import BytesIO, TextIOWrapper

app = Flask(__name__)
CORS(app)

CSV_FILE = 'historico_lotofacil.csv'
CAIXA_DOWNLOAD_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/resultados/download?modalidade=Lotof%C3%A1cil"

def atualizar_caixa( ):
    """Baixa o arquivo ZIP da Caixa, extrai o CSV e salva o histórico."""
    print("Tentando baixar histórico completo da Caixa...")
    try:
        # 1. Baixar o arquivo ZIP
        response = requests.get(CAIXA_DOWNLOAD_URL, timeout=30)
        response.raise_for_status()
        
        # 2. Abrir o ZIP em memória
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            # O nome do arquivo CSV dentro do ZIP é geralmente "D_LOTOFACIL.CSV"
            csv_name = [name for name in z.namelist() if name.endswith('.CSV') or name.endswith('.csv')][0]
            
            # 3. Ler o CSV
            with z.open(csv_name) as csv_file:
                # O CSV da Caixa usa ponto e vírgula (;) como delimitador e codificação Latin-1 (ISO-8859-1)
                reader = csv.reader(TextIOWrapper(csv_file, 'latin-1'), delimiter=';')
                linhas = list(reader)
        
        # 4. Processar e salvar no formato do projeto (tabulação)
        if not linhas:
            print("Erro: Arquivo CSV da Caixa vazio.")
            return False

        # Colunas relevantes: Concurso (0), Data Sorteio (1), Dezenas (2 a 16)
        
        # Ignora o cabeçalho (primeira linha)
        dados_processados = []
        for linha in linhas[1:]:
            if len(linha) >= 17:
                try:
                    concurso = int(linha[0])
                    data = linha[1]
                    # As dezenas estão nas colunas 2 a 16 (índices 2 a 16)
                    numeros = [int(n) for n in linha[2:17]]
                    
                    # Formato de saída: [concurso, data, n1, n2, ..., n15]
                    dados_processados.append([concurso, data] + numeros)
                except ValueError:
                    # Ignora linhas com dados inválidos
                    continue

        # 5. Salvar no CSV do projeto (usando tabulação)
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            # Escreve o cabeçalho do projeto
            writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])
            # Escreve os dados
            writer.writerows(dados_processados)

        print(f"Histórico completo da Caixa salvo com sucesso! Total de {len(dados_processados)} concursos.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a URL da Caixa: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao processar o arquivo da Caixa: {e}")
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
                    # Números estão nas colunas 2 a 16 (índices 2 a 16)
                    numeros = [int(n) for n in linha[2:17]]
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
        return {
            "ultimo_concurso": 0,
            "data_ultimo": "N/A",
            "ultimos_numeros": [],
            "quentes": [],
            "frios": [],
            "total_sorteios": 0,
            "erro": "Histórico de sorteios está vazio ou não pôde ser carregado. Tente atualizar manualmente a rota /api/atualizar."
        }

    todos_numeros = [n for jogo in historico for n in jogo['numeros']]
    contagem = {n: todos_numeros.count(n) for n in range(1, 26)}
    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    frios = sorted(contagem.items(), key=lambda x: x[1])[:10]

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
            "apostas": apostas
        }

    # Fixos dos últimos 50
    ultimos_50 = historico[-50:]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
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
    sucesso = atualizar_caixa()
    return jsonify({"atualizado": sucesso, "fonte": "Caixa Econômica Federal - Histórico Completo"})

@app.route('/api/palpites', methods=['GET'])
def palpites():
    # Garante que o histórico está carregado (ou tenta atualizar) antes de gerar palpites
    if not os.path.exists(CSV_FILE):
        atualizar_caixa()
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    # Garante que o histórico está carregado (ou tenta atualizar) antes de gerar estatísticas
    if not os.path.exists(CSV_FILE):
        atualizar_caixa()
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Caixa Download", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))

