from flask import Flask, jsonify
from flask_cors import CORS
import requests
import csv
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

CSV_FILE = 'historico_lotofacil.csv'
CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"

def atualizar_tudo_da_caixa():
    try:
        print("Atualizando histórico completo da Caixa...")
        response = requests.get(CAIXA_API, timeout=15)
        if response.status_code != 200:
            return False
        
        data = response.json()
        ultimo_concurso = data['numero']
        dezenas = sorted(data['listaDezenas'])
        data_sorteio = data['dataApuracao']  # formato: dd/mm/yyyy

        # Formata data pro CSV
        data_formatada = datetime.strptime(data_sorteio, '%d/%m/%Y').strftime('%d/%m/%Y')

        novo_registro = [ultimo_concurso, data_formatada] + dezenas

        # Se não tem CSV, cria com cabeçalho
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['concurso', 'data'] + [f'n{i}' for i in range(1,16)])
                writer.writerow(novo_registro)
            print(f"CSV criado com concurso {ultimo_concurso}")
            return True

        # Lê concursos existentes
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            linhas = list(reader)
            concursos_existentes = [int(row[0]) for row in linhas[1:] if row and row[0].isdigit()]

        # Se já tem o último, só atualiza se for mais novo
        if ultimo_concurso in concursos_existentes:
            print(f"Já está atualizado até o concurso {ultimo_concurso}")
            return False

        # Adiciona o novo
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(novo_registro)
        
        print(f"Novo concurso adicionado: {ultimo_concurso}")
        return True

    except Exception as e:
        print("Erro ao atualizar da Caixa:", e)
        return False

# Rota que atualiza e retorna tudo
@app.route('/api/atualizar', methods=['GET'])
def atualizar():
    sucesso = atualizar_tudo_da_caixa()
    return jsonify({"atualizado": sucesso, "fonte": "Caixa Oficial"})

# Mantém suas rotas de palpites e resultados (sem mudar nada)
# (usa o mesmo código que já temos de gerar_apostas e estatisticas)

@app.route('/api/palpites', methods=['GET'])
def palpites():
    atualizar_tudo_da_caixa()  # sempre atualiza antes
    # ... resto do código de gerar_apostas (igual antes)
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    atualizar_tudo_da_caixa()
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - API Caixa Oficial", "online": True})