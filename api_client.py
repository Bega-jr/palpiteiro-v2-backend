import requests

API_URL = "URL_DA_SUA_API_AQUI"  # coloque sua API real

def buscar_dados_api():
try:
response = requests.get(API_URL, timeout=5)
response.raise_for_status()
return response.json()
except Exception as exc:
print(f"[API] Erro ao acessar API: {exc}")
return None
