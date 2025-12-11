# api/health.py
from flask import Flask, jsonify
from flask_cors import CORS
from excel_manager import carregar_excel_struct

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def health():
    df = carregar_excel_struct()
    rows = int(df.shape[0]) if df is not None else 0
    return jsonify({"status": "ok", "excel_rows": rows})
