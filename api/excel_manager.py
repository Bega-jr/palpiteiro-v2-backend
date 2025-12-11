# api/excel_manager.py
import pandas as pd
import os
from typing import Optional

EXCEL_FILE = os.environ.get("EXCEL_FILE", "Lotofácil.xlsx")  # arquivo no repo (fallback)

BOLA_COLS = [f"Bola{i}" for i in range(1, 16)]
EXPECTED_COLS = ["Concurso", "Data Sorteio"] + BOLA_COLS + [
    "Ganhadores 15 acertos", "Rateio 15 acertos",
    "Ganhadores 14 acertos", "Rateio 14 acertos",
    "Ganhadores 13 acertos", "Rateio 13 acertos",
    "Ganhadores 12 acertos", "Rateio 12 acertos",
    "Ganhadores 11 acertos", "Rateio 11 acertos"
]

def carregar_excel_struct():
    if not os.path.exists(EXCEL_FILE):
        print("Excel não encontrado:", EXCEL_FILE)
        return None
    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        for col in EXPECTED_COLS:
            if col not in df.columns:
                df[col] = None
        def extract_list(row):
            nums = []
            for c in BOLA_COLS:
                val = row.get(c)
                if pd.isna(val):
                    continue
                try:
                    nums.append(int(val))
                except:
                    pass
            return sorted(nums)
        df["numeros"] = df.apply(extract_list, axis=1)
        return df
    except Exception as e:
        print("Erro ao ler Excel:", e)
        return None

def listar_concursos_dict():
    df = carregar_excel_struct()
    if df is None or df.empty:
        return []
    df2 = df.sort_values("Concurso", ascending=False)
    out = []
    for _, row in df2.iterrows():
        out.append({
            "concurso": int(row.get("Concurso")),
            "data": str(row.get("Data Sorteio")),
            "numeros": row.get("numeros") or [],
            "ganhadores_15": int(row.get("Ganhadores 15 acertos") or 0),
            "premio_15": str(row.get("Rateio 15 acertos") or "R$0,00"),
            "ganhadores_14": int(row.get("Ganhadores 14 acertos") or 0),
            "premio_14": str(row.get("Rateio 14 acertos") or "R$0,00"),
            "ganhadores_13": int(row.get("Ganhadores 13 acertos") or 0),
            "premio_13": str(row.get("Rateio 13 acertos") or "R$0,00"),
            "ganhadores_12": int(row.get("Ganhadores 12 acertos") or 0),
            "premio_12": str(row.get("Rateio 12 acertos") or "R$0,00"),
            "ganhadores_11": int(row.get("Ganhadores 11 acertos") or 0),
            "premio_11": str(row.get("Rateio 11 acertos") or "R$0,00"),
        })
    return out
