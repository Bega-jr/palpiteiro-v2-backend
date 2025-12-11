import pandas as pd
import os

EXCEL_FILE = "Lotofácil.xlsx"

# Colunas padrão esperadas no Excel

COLUNAS_PADRAO = [
"Concurso", "Data Sorteio",
"Bola1", "Bola2", "Bola3", "Bola4", "Bola5",
"Bola6", "Bola7", "Bola8", "Bola9", "Bola10",
"Bola11", "Bola12", "Bola13", "Bola14", "Bola15",
"Ganhadores 15 acertos", "Rateio 15 acertos",
"Ganhadores 14 acertos", "Rateio 14 acertos",
"Ganhadores 13 acertos", "Rateio 13 acertos",
"Ganhadores 12 acertos", "Rateio 12 acertos",
"Ganhadores 11 acertos", "Rateio 11 acertos"
]

def carregar_excel():
"""Carrega o Excel ou cria um novo DataFrame vazio."""
if not os.path.exists(EXCEL_FILE):
print("⚠ Excel não encontrado, criando novo arquivo...")
return pd.DataFrame(columns=COLUNAS_PADRAO)

```
try:
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

    # Garante que todas as colunas existem
    for col in COLUNAS_PADRAO:
        if col not in df.columns:
            df[col] = None

    df = df[COLUNAS_PADRAO]  # Ordena colunas
    return df

except Exception as e:
    print("Erro ao carregar Excel:", e)
    return pd.DataFrame(columns=COLUNAS_PADRAO)
```

def salvar_excel(df):
"""Salva o DataFrame no Excel."""
try:
df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
print("✓ Excel atualizado com sucesso!")
return True
except Exception as e:
print("❌ Erro ao salvar Excel:", e)
return False

def adicionar_concurso(dados):
"""
Adiciona um concurso ao Excel, evitando duplicações.
`dados` deve conter:
- concurso
- data
- numeros (lista 15)
- ganhadores por faixa
- premios por faixa
"""
df = carregar_excel()

```
concurso = int(dados["concurso"])

# Verifica duplicação
if concurso in df["Concurso"].values:
    print(f"⚠ Concurso {concurso} já existe. Ignorando.")
    return False

# Monta linha
linha = {
    "Concurso": concurso,
    "Data Sorteio": dados["data"]
}

# Adiciona bolas
for i, n in enumerate(dados["numeros"], start=1):
    linha[f"Bola{i}"] = n

# Adiciona faixas
linha["Ganhadores 15 acertos"] = dados["ganhadores_15"]
linha["Rateio 15 acertos"] = dados["premio_15"]

linha["Ganhadores 14 acertos"] = dados["ganhadores_14"]
linha["Rateio 14 acertos"] = dados["premio_14"]

linha["Ganhadores 13 acertos"] = dados["ganhadores_13"]
linha["Rateio 13 acertos"] = dados["premio_13"]

linha["Ganhadores 12 acertos"] = dados["ganhadores_12"]
linha["Rateio 12 acertos"] = dados["premio_12"]

linha["Ganhadores 11 acertos"] = dados["ganhadores_11"]
linha["Rateio 11 acertos"] = dados["premio_11"]

# Adiciona no DataFrame
df = pd.concat([df, pd.DataFrame([linha])], ignore_index=True)

# Ordena por concurso
df = df.sort_values("Concurso", ascending=True)

return salvar_excel(df)
```
