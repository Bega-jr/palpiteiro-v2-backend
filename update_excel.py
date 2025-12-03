import requests
import os
from datetime import datetime

# Link direto do Excel oficial da Caixa (sempre atualizado)
URL_EXCEL = "https://caixa.gov.br/Downloads/lotofacil/Lotofacil.xls"

def atualizar_excel():
    try:
        print(f"[{datetime.now()}] Baixando Excel oficial da Caixa...")
        response = requests.get(URL_EXCEL, timeout=60)
        response.raise_for_status()

        with open('Lotofácil.xlsx', 'wb') as f:
            f.write(response.content)

        print(f"[{datetime.now()}] Excel atualizado com sucesso! Tamanho: {len(response.content)} bytes")
    except Exception as e:
        print(f"[{datetime.now()}] Erro ao atualizar Excel: {e}")

if __name__ == "__main__":
    atualizar_excel()