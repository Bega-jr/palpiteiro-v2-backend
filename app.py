from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import random
import pandas as pd
from io import BytesIO
import zipfile
import csv
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app)

# --- CONFIGURAÇÕES ---
EXCEL_FILE = 'Lotofácil.xlsx'
CAIXA_DOWNLOAD_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/resultados/download?modalidade=Lotof%C3%A1cil"
CONCURSO_COLUMN = "Concurso"

# --- FUNÇÕES DE ATUALIZAÇÃO E CARREGAMENTO ---

def atualizar_excel( ):
    """Baixa o arquivo ZIP da Caixa, extrai o CSV e salva no Excel."""
    print("Tentando baixar histórico completo da Caixa...")
    try:
        # 1. Baixar o arquivo ZIP
        response = requests.get(CAIXA_DOWNLOAD_URL, timeout=30)
        response.raise_for_status()
        
        # 2. Abrir o ZIP em memória
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            csv_name = [name for name in z.namelist() if name.endswith('.CSV') or name.endswith('.csv')][0]
            
            # 3. Ler o CSV com pandas
            with z.open(csv_name) as csv_file:
                # O CSV da Caixa usa ponto e vírgula (;) como delimitador e codificação Latin-1
                df = pd.read_csv(csv_file, sep=';', encoding='latin-1', header=0)
        
        # 4. Limpeza e Seleção de Colunas
        # Renomear a coluna de concurso para o padrão
        df.rename(columns={'Concurso': CONCURSO_COLUMN}, inplace=True)
        
        # Selecionar apenas as colunas necessárias para o palpiteiro
        colunas_dezenas = [f'Bola{i}' for i in range(1, 16)]
        colunas_selecionadas = [CONCURSO_COLUMN, 'Data Sorteio'] + colunas_dezenas
        
        df_final = df[colunas_selecionadas].copy()
        
        # Renomear as colunas de dezenas para n1, n2, etc. (Opcional, mas ajuda)
        df_final.columns = [CONCURSO_COLUMN, 'Data Sorteio'] + [f'n{i}' for i in range(1, 16)]
        
        # 5. Salvar no Excel
        df_final.to_excel(EXCEL_FILE, index=False)

        print(f"Histórico completo da Caixa salvo com sucesso em {EXCEL_FILE}!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a URL da Caixa: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao processar o arquivo da Caixa: {e}")
        return False

def carregar_historico() -> List[Dict[str, Any]]:
    """Carrega o histórico do Excel e retorna uma lista de dicionários."""
    if not os.path.exists(EXCEL_FILE):
        # Tenta atualizar se o arquivo não existir
        if atualizar_excel():
            return carregar_historico()
        return []
    
    try:
        df = pd.read_excel(EXCEL_FILE)
        
        # Garante que as colunas de dezenas são tratadas como números
        colunas_dezenas = [f'n{i}' for i in range(1, 16)]
        for col in colunas_dezenas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
        historico = []
        for index, row in df.iterrows():
            numeros = [row[f'n{i}'] for i in range(1, 16) if pd.notna(row[f'n{i}'])]
            historico.append({
                'concurso': row[CONCURSO_COLUMN],
                'data': row['Data Sorteio'],
                'numeros': sorted([int(n) for n in numeros])
            })
        
        return historico
    except Exception as e:
        print(f"Erro ao carregar o Excel: {e}")
        return []

# --- FUNÇÕES DE ESTATÍSTICAS E PALPITES ---

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
            "erro": "Histórico de sorteios está vazio ou não pôde ser carregado."
        }

    todos_numeros = [n for jogo in historico for n in jogo['numeros']]
    contagem = {n: todos_numeros.count(n) for n in range(1, 26)}
    
    # 10 números mais sorteados (quentes)
    quentes = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    # 10 números menos sorteados (frios)
    frios = sorted(contagem.items(), key=lambda x: x[1])[:10]

    ultimo = historico[-1]
    return {
        "ultimo_concurso": int(ultimo['concurso']),
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": ultimo['numeros'],
        "quentes": [n for n, c in quentes],
        "frios": [n for n, c in frios],
        "total_sorteios": len(historico)
    }

def gerar_apostas():
    stats = estatisticas()
    
    if stats.get("erro"):
        return {"erro": stats["erro"]}

    # 1. Definir os fixos (4 números mais quentes)
    fixos_nums = stats['quentes'][:4]
    
    # 2. Gerar 7 apostas
    apostas = []
    
    # Função auxiliar para criar uma aposta completa
    def criar_aposta(base: List[int]) -> List[int]:
        aposta = base[:]
        candidatos = [n for n in range(1, 26) if n not in aposta]
        
        # Prioriza números que não estão nos fixos para completar
        random.shuffle(candidatos)
        
        while len(aposta) < 15:
            aposta.append(candidatos.pop())
        
        return sorted(aposta)

    # 5 apostas com os fixos
    for _ in range(5):
        apostas.append(criar_aposta(fixos_nums))
        
    # 2 apostas aleatórias (sem fixos)
    for _ in range(2):
        apostas.append(criar_aposta([]))

    return {
        "gerado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "fixos": fixos_nums,
        "apostas": apostas
    }

# --- ROTAS DA API ---

@app.route('/api/atualizar', methods=['GET'])
def atualizar():
    sucesso = atualizar_excel()
    return jsonify({"atualizado": sucesso, "fonte": "Caixa Econômica Federal - Histórico Completo"})

@app.route('/api/palpites', methods=['GET'])
def palpites():
    # Garante que o histórico está carregado (ou tenta atualizar) antes de gerar palpites
    if not os.path.exists(EXCEL_FILE):
        atualizar_excel()
    return jsonify(gerar_apostas())

@app.route('/api/resultados', methods=['GET'])
def resultados():
    # Garante que o histórico está carregado (ou tenta atualizar) antes de gerar estatísticas
    if not os.path.exists(EXCEL_FILE):
        atualizar_excel()
    return jsonify(estatisticas())

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 Backend - Excel/Pandas", "online": True})

if __name__ == '__main__':
    # Tenta atualizar o Excel na inicialização
    atualizar_excel()
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))

