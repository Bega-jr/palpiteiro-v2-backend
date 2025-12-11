import requests
from excel_manager import adicionar_concurso, carregar_excel

URL_CAIXA = "[https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest](https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest)"

def obter_estatisticas():
"""
Busca o último concurso na API da Caixa.
Se der erro: retorna fallback amigável.
Se funcionar: adiciona ao Excel e devolve JSON.
"""

```
try:
    print("🔄 Consultando API oficial...")
    resp = requests.get(URL_CAIXA, timeout=10)

    if resp.status_code != 200:
        return {"status": "erro_api", "mensagem": "Falha ao consultar API da Caixa"}

    data = resp.json()

    numeros = data.get("listaDezenas", [])
    if not numeros:
        return {"status": "erro_api", "mensagem": "Formato inesperado na API"}

    numeros = [int(n) for n in numeros]

    concurso = int(data["numero"])
    data_sorteio = data["dataApuracao"]

    # Monta objeto interno para o Excel
    dados = {
        "concurso": concurso,
        "data": data_sorteio,
        "numeros": sorted(numeros),

        "ganhadores_15": data.get("numeroGanhadores15Acertos", 0),
        "premio_15": data.get("valorRateio15Acertos", 0),

        "ganhadores_14": data.get("numeroGanhadores14Acertos", 0),
        "premio_14": data.get("valorRateio14Acertos", 0),

        "ganhadores_13": data.get("numeroGanhadores13Acertos", 0),
        "premio_13": data.get("valorRateio13Acertos", 0),

        "ganhadores_12": data.get("numeroGanhadores12Acertos", 0),
        "premio_12": data.get("valorRateio12Acertos", 0),

        "ganhadores_11": data.get("numeroGanhadores11Acertos", 0),
        "premio_11": data.get("valorRateio11Acertos", 0),
    }

    # Atualiza Excel 🟢
    adicionar_concurso(dados)

    return {
        "status": "ok",
        "mensagem": "Dados atualizados com sucesso",
        "concurso": concurso,
        "data": data_sorteio,
        "numeros": numeros
    }

except Exception as e:
    print("❌ Erro ao consultar API:", e)

    df = carregar_excel()
    if df is None or df.empty:
        return {"status": "erro_total", "mensagem": "Sem API e Excel vazio"}

    ultimo = df.iloc[-1]
    fallback = {
        "status": "fallback_excel",
        "mensagem": "API fora do ar, usando Excel local",
        "concurso": int(ultimo["Concurso"])
    }

    return fallback
```
