# api/api_client.py
import requests
import os

API_BASE = os.environ.get("API_BASE_URL", "https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest")
TIMEOUT = int(os.environ.get("API_TIMEOUT", 8))

def obter_dados_externos():
    try:
        r = requests.get(API_BASE, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Erro API externa:", e)
        return None
