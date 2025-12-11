import pandas as pd
import os

EXCEL_PATH = "Lotofacil.xlsx"

def salvar_excel(dados):
try:
df = pd.DataFrame(dados)
df.to_excel(EXCEL_PATH, index=False)
print("[Excel] Arquivo atualizado com sucesso.")
except Exception as e:
print(f"[Excel] Erro ao salvar excel: {e}")

def ler_excel():
try:
if not os.path.exists(EXCEL_PATH):
print("[Excel] Arquivo não encontrado.")
return None

```
    df = pd.read_excel(EXCEL_PATH)
    return df.to_dict(orient='records')

except Exception as e:
    print(f"[Excel] Erro ao ler excel: {e}")
    return None
```
