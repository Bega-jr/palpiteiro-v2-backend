from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

EXCEL_FILE = 'Lotofácil.xlsx'

def carregar_lotofacil():
    if not os.path.exists(EXCEL_FILE):
        return []

    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        lotofacil = []
        for _, row in df.iterrows():
            try:
                # Números sorteados (15 bolas na ordem oficial)
                numeros = [int(row[f'Bola{i}']) for i in range(1, 16)]

                concurso = int(row['Concurso'])
                data = str(row['Data Sorteio']).split(' ')[0]

                # Faixas de premiação (11 a 15 acertos)
                def get_ganhadores(faixa):
                    col = f'Ganhadores {faixa} acertos'
                    return int(row[col]) if col in row and pd.notna(row[col]) else 0

                def get_rateio(faixa):
                    col = f'Rateio {faixa} acertos'
                    return str(row[col]) if col in row and pd.notna(row[col]) else 'R$0,00'

                # Cidades premiadas (15 acertos)
                cidades_raw = str(row.get('Cidade / UF', ''))
                cidades = []
                if cidades_raw and cidades_raw != 'nan':
                    for item in cidades_raw.split(';'):
                        item = item.strip()
                        if '/' in item:
                            cidade, uf = item.split('/', 1)
                            cidades.append({
                                "cidade": cidade.strip(),
                                "uf": uf.strip(),
                                "ganhadores": get_ganhadores(15)  # Total de ganhadores 15 acertos
                            })

                # Observação (sorteio especial, estimativa, etc)
                observacao = str(row.get('Observação', ''))

                lotofacil.append({
                    'concurso': concurso,
                    'data': data,
                    'numeros': numeros,
                    # Faixas de premiação
                    'ganhadores_15': get_ganhadores(15),
                    'rateio_15': get_rateio(15),
                    'ganhadores_14': get_ganhadores(14),
                    'rateio_14': get_rateio(14),
                    'ganhadores_13': get_ganhadores(13),
                    'rateio_13': get_rateio(13),
                    'ganhadores_12': get_ganhadores(12),
                    'rateio_12': get_rateio(12),
                    'ganhadores_11': get_ganhadores(11),
                    'rateio_11': get_rateio(11),
                    # Outros dados
                    'arrecadacao_total': str(row.get('Arrecadacao Total', 'R$0,00')),
                    'estimativa_premio': str(row.get('Estimativa Prêmio', 'R$0,00')),
                    'acumulado_15': str(row.get('Acumulado 15 acertos', 'NÃO')),
                    'acumulado_especial': str(row.get('Acumulado sorteio especial Lotofácil da Independência', 'R$0,00')),
                    'observacao': observacao,
                    'cidades_premiadas': cidades
                })
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                continue

        print(f"Carregados {len(lotofacil)} concursos da Lotofácil")
        return sorted(lotofacil, key=lambda x: x['concurso'], reverse=True)

    except Exception as e:
        print("Erro ao ler Excel:", e)
        return []

@app.route('/api/resultados', methods=['GET'])
def resultados():
    dados = carregar_lotofacil()
    if not dados:
        return jsonify({"erro": "Arquivo Excel não encontrado ou corrompido"})

    ultimo = dados[0]

    faixas = [
        {
            "faixa": "15 acertos",
            "ganhadores": ultimo['ganhadores_15'],
            "premio": ultimo['rateio_15'],
            "cidades": ultimo['cidades_premiadas']
        },
        {
            "faixa": "14 acertos",
            "ganhadores": ultimo['ganhadores_14'],
            "premio": ultimo['rateio_14']
        },
        {
            "faixa": "13 acertos",
            "ganhadores": ultimo['ganhadores_13'],
            "premio": ultimo['rateio_13']
        },
        {
            "faixa": "12 acertos",
            "ganhadores": ultimo['ganhadores_12'],
            "premio": ultimo['rateio_12']
        },
        {
            "faixa": "11 acertos",
            "ganhadores": ultimo['ganhadores_11'],
            "premio": ultimo['rateio_11']
        }
    ]

    return jsonify({
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "ultimos_numeros": ultimo['numeros'],
        "ganhadores": faixas,
        "arrecadacao_total": ultimo['arrecadacao_total'],
        "estimativa_premio": ultimo['estimativa_premio'],
        "acumulou_15": ultimo['acumulado_15'] == 'SIM',
        "acumulado_especial": ultimo['acumulado_especial'],
        "observacao": ultimo['observacao'],
        "data_referencia": ultimo['data']
    })

@app.route('/api/palpites', methods=['GET'])
def palpites():
    dados = carregar_lotofacil()
    if len(dados) < 10:
        return jsonify({"erro": "Histórico insuficiente"})

    ultimos_50 = dados[:50]
    contagem = {}
    for jogo in ultimos_50:
        for n in jogo['numeros']:
            contagem[n] = contagem.get(n, 0) + 1

    fixos = [n for n, c in sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:5]]

    def criar_aposta(base=[]):
        aposta = base[:]
        candidatos = [n for n in range(1, 26) if n not in aposta]
        while len(aposta) < 15:
            escolhido = random.choice(candidatos)
            aposta.append(escolhido)
            candidatos.remove(escolhido)
        return sorted(aposta)

    apostas = []
    for i in range(7):
        base = fixos if i < 5 else []
        apostas.append(criar_aposta(base))

    ultimo = dados[0]
    return jsonify({
        "gerado_em": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "ultimo_concurso": ultimo['concurso'],
        "data_ultimo": ultimo['data'],
        "fixos": fixos,
        "apostas": apostas
    })

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - Excel Oficial Caixa", "online": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))