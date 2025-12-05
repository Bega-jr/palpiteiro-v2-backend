from flask import Flask, jsonify
import os

app = Flask(__name__)

# FORÇA O CORS (funciona 100% no Vercel)
from flask_cors import CORS
CORS(app)

# DADOS FIXOS (funciona enquanto o Excel não sobe)
dados_fixos = {
    "concurso": 3552,
    "data": "05/12/2025",
    "numeros": [1, 3, 5, 7, 8, 9, 11, 13, 15, 17, 19, 20, 22, 23, 25],
    "ganhadores": [
        {"faixa": "15 acertos", "ganhadores": 0, "premio": "R$0,00"},
        {"faixa": "14 acertos", "ganhadores": 3, "premio": "R$35.000,00"},
        {"faixa": "13 acertos", "ganhadores": 187, "premio": "R$25,00"},
        {"faixa": "12 acertos", "ganhadores": 6500, "premio": "R$10,00"},
        {"faixa": "11 acertos", "ganhadores": 78000, "premio": "R$5,00"}
    ]
}

@app.route('/api/resultados')
def resultados():
    return jsonify(dados_fixos)

@app.route('/api/palpites-vip')
def palpites_vip():
    quentes = [3, 5, 7, 11, 13, 15, 17, 25]
    def gerar():
        aposta = quentes[:6]
        while len(aposta) < 15:
            n = random.randint(1, 25)
            if n not in aposta:
                aposta.append(n)
        return sorted(aposta)
    
    return jsonify({
        "quentes": quentes,
        "apostas": [gerar() for _ in range(7)]
    })

@app.route('/')
def home():
    return jsonify({"status": "Palpiteiro V2 - 100% Online"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))