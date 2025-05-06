from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# Configurações do jogo
SYMBOLS = ["🌾", "🍞", "🥖", "🌟", "🍚"]  # Símbolos do Triguinho
REWARDS = {
    ("🌾", "🌾", "🌾"): 50,
    ("🍞", "🍞", "🍞"): 30,
    ("🥖", "🥖", "🥖"): 20,
    ("🌟", "🌟", "🌟"): 100,
    ("🍚", "🍚", "🍚"): 40
}
SPIN_COST = 10  # Custo por giro
INITIAL_BALANCE = 100  # Saldo inicial
RTP = 0.95  # Return to Player (95% dos giros retornam como prêmios a longo prazo)

# Estado da banca (simulado)
banca = {"balance": 10000, "total_spins": 0, "total_payouts": 0}

# Estado do jogador
player = {"balance": INITIAL_BALANCE}

@app.route("/")
def index():
    return render_template("index.html", balance=player["balance"])

@app.route("/spin", methods=["POST"])
def spin():
    if player["balance"] < SPIN_COST:
        return jsonify({"error": "Saldo insuficiente! Recarregue seu saldo."})

    # Deduz o custo do giro
    player["balance"] -= SPIN_COST
    banca["balance"] += SPIN_COST
    banca["total_spins"] += 1

    # Gera resultado dos rolos
    result = [random.choice(SYMBOLS) for _ in range(3)]
    combination = tuple(result)
    payout = REWARDS.get(combination, 0)

    # Controla a banca (simulação simples de RTP)
    if payout > 0 and random.random() < RTP:
        if banca["balance"] >= payout:
            player["balance"] += payout
            banca["balance"] -= payout
            banca["total_payouts"] += payout
        else:
            payout = 0  # Banca não pode pagar

    return jsonify({
        "result": result,
        "payout": payout,
        "balance": player["balance"],
        "message": f"Você ganhou {payout} créditos!" if payout > 0 else "Tente novamente!"
    })

@app.route("/deposit", methods=["POST"])
def deposit():
    amount = int(request.form.get("amount", 0))
    if amount > 0:
        player["balance"] += amount
        return jsonify({"balance": player["balance"], "message": f"Depósito de {amount} créditos realizado!"})
    return jsonify({"error": "Valor inválido!"})

if __name__ == "__main__":
    app.run(debug=True)