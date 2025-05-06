from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import random
from datetime import datetime
import hashlib
import mercadopago
import logging
import uuid

app = Flask(__name__)
app.secret_key = "triguinho_secret_key_2025"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

# Configurações do jogo
SYMBOLS = ["🌾", "🍞", "🥖", "🌟", "🍚"]
REWARDS = {
    ("🌾", "🌾", "🌾"): 50,
    ("🍞", "🍞", "🍞"): 30,
    ("🥖", "🥖", "🥖"): 20,
    ("🌟", "🌟", "🌟"): 100,
    ("🍚", "🍚", "🍚"): 40
}
SPIN_COST = 10
INITIAL_BALANCE = 100
RTP = 0.95
DAILY_DEPOSIT_LIMIT = 500
MERCHANT_PIX_KEY = "52d84f0b-cebf-4057-adda-f5d368b5bb8c"

# Configuração do Mercado Pago
mp = mercadopago.SDK("TEST-1341189477037903-050610-d109b71ed6ab7f7df17057bce80e3cfe-374217328")  # Substitua pelo seu access_token de teste

# Inicializa o banco de dados
def init_db():
    try:
        with sqlite3.connect("database/triguinho.db") as conn:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                pix_key TEXT,
                balance REAL DEFAULT 100,
                total_deposits_today REAL DEFAULT 0,
                last_deposit_date TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                timestamp TIMESTAMP,
                result TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS banca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                balance REAL DEFAULT 10000,
                total_spins INTEGER DEFAULT 0,
                total_payouts REAL DEFAULT 0
            )""")
            c.execute("INSERT OR IGNORE INTO banca (id, balance) VALUES (1, 10000)")
            conn.commit()
            app.logger.info("Banco de dados inicializado com sucesso.")
    except Exception as e:
        app.logger.error(f"Erro ao inicializar o banco de dados: {e}")

init_db()

class User(UserMixin):
    def __init__(self, id, username, balance, pix_key):
        self.id = id
        self.username = username
        self.balance = balance
        self.pix_key = pix_key

@login_manager.user_loader
def load_user(user_id):
    try:
        with sqlite3.connect("database/triguinho.db") as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, balance, pix_key FROM users WHERE id = ?", (user_id,))
            user = c.fetchone()
            if user:
                return User(user[0], user[1], user[2], user[3])
            return None
    except Exception as e:
        app.logger.error(f"Erro ao carregar usuário: {e}")
        return None

def check_deposit_limit(user_id, amount):
    try:
        with sqlite3.connect("database/triguinho.db") as conn:
            c = conn.cursor()
            c.execute("SELECT last_deposit_date, total_deposits_today FROM users WHERE id = ?", (user_id,))
            result = c.fetchone()
            today = datetime.now().strftime("%Y-%m-%d")
            if result:
                last_date, total_today = result
                if last_date != today:
                    c.execute("UPDATE users SET total_deposits_today = 0, last_deposit_date = ? WHERE id = ?", (today, user_id))
                    total_today = 0
                if total_today + amount > DAILY_DEPOSIT_LIMIT:
                    return False
                return True
            return True
    except Exception as e:
        app.logger.error(f"Erro ao verificar limite de depósito: {e}")
        return False

def log_transaction(user_id, type, amount, result=""):
    try:
        with sqlite3.connect("database/triguinho.db") as conn:
            c = conn.cursor()
            c.execute("INSERT INTO transactions (user_id, type, amount, timestamp, result) VALUES (?, ?, ?, ?, ?)",
                      (user_id, type, amount, datetime.now(), result))
            conn.commit()
    except Exception as e:
        app.logger.error(f"Erro ao registrar transação: {e}")

@app.route("/")
@login_required
def index():
    return render_template("index.html", balance=current_user.balance)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = hashlib.sha256(request.form.get("password").encode()).hexdigest()
        try:
            with sqlite3.connect("database/triguinho.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id, username, balance, pix_key FROM users WHERE username = ? AND password = ?", (username, password))
                user = c.fetchone()
                if user:
                    user_obj = User(user[0], user[1], user[2], user[3])
                    login_user(user_obj)
                    return redirect(url_for("index"))
                flash("Credenciais inválidas.", "error")
        except Exception as e:
            app.logger.error(f"Erro ao fazer login: {e}")
            flash("Erro ao processar login.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = hashlib.sha256(request.form.get("password").encode()).hexdigest()
        pix_key = request.form.get("pix_key")
        if not pix_key:
            flash("Chave Pix é obrigatória.", "error")
            return render_template("register.html")
        try:
            with sqlite3.connect("database/triguinho.db") as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password, pix_key, balance, last_deposit_date) VALUES (?, ?, ?, ?, ?)",
                          (username, password, pix_key, INITIAL_BALANCE, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                flash("Registro concluído! Faça login.", "success")
                return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Usuário já existe.", "error")
        except Exception as e:
            app.logger.error(f"Erro ao registrar usuário: {e}")
            flash("Erro ao processar registro.", "error")
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/spin", methods=["POST"])
@login_required
def spin():
    try:
        with sqlite3.connect("database/triguinho.db") as conn:
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE id = ?", (current_user.id,))
            balance = c.fetchone()[0]
            if balance < SPIN_COST:
                return jsonify({"error": "Saldo insuficiente! Recarregue seu saldo."})

            c.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (SPIN_COST, current_user.id))
            c.execute("UPDATE banca SET balance = balance + ?, total_spins = total_spins + 1 WHERE id = 1", (SPIN_COST,))
            log_transaction(current_user.id, "spin", -SPIN_COST)

            result = [random.choice(SYMBOLS) for _ in range(3)]
            combination = tuple(result)
            payout = REWARDS.get(combination, 0)

            c.execute("SELECT balance FROM banca WHERE id = 1")
            banca_balance = c.fetchone()[0]
            if payout > 0 and random.random() < RTP and banca_balance >= payout:
                c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (payout, current_user.id))
                c.execute("UPDATE banca SET balance = balance - ?, total_payouts = total_payouts + ? WHERE id = 1", (payout, payout))
                log_transaction(current_user.id, "payout", payout, str(result))
            else:
                payout = 0

            c.execute("SELECT balance FROM users WHERE id = ?", (current_user.id,))
            current_user.balance = c.fetchone()[0]
            conn.commit()

            app.logger.info(f"Giro realizado: {result}, Pagamento: {payout}, Saldo: {current_user.balance}")
            return jsonify({
                "result": result,
                "payout": payout,
                "balance": current_user.balance,
                "message": f"Você ganhou {payout} reais!" if payout > 0 else "Tente novamente!"
            })
    except Exception as e:
        app.logger.error(f"Erro na rota /spin: {e}")
        return jsonify({"error": "Erro ao processar o giro."})

@app.route("/deposit_pix", methods=["POST"])
@login_required
def deposit_pix():
    try:
        amount = float(request.form.get("amount", 0))
        if amount <= 0:
            return jsonify({"error": "Valor inválido!"})
        if not check_deposit_limit(current_user.id, amount):
            return jsonify({"error": f"Limite diário de depósito ({DAILY_DEPOSIT_LIMIT} reais) excedido!"})

        payment_data = {
            "transaction_amount": amount,
            "description": "Depósito Jogo do Triguinho",
            "payment_method_id": "pix",
            "payer": {
                "email": f"{current_user.username}@example.com",
                "first_name": current_user.username,
                "identification": {"type": "CPF", "number": "12345678900"}
            },
            "notification_url": "https://your-app.com/webhook"
        }
        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {"X-Idempotency-Key": str(uuid.uuid4())}
        result = mp.payment().create(payment_data, request_options)
        payment = result["response"]

        if payment["status"] == "pending":
            qr_code = payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
            if not qr_code:
                app.logger.error("QR code não encontrado na resposta do Mercado Pago.")
                return jsonify({"error": "Erro ao gerar o código Pix."})
            app.logger.info(f"Pagamento Pix criado: ID {payment['id']}, Valor: {amount}, Código: {qr_code}")
            return jsonify({
                "qr_code": qr_code,
                "payment_id": payment["id"],
                "message": "Copie o código Pix ou escaneie o QR code."
            })
        app.logger.error(f"Pagamento Pix não criado: {payment}")
        return jsonify({"error": f"Erro ao criar o pagamento Pix: Status {payment['status']}"})
    except Exception as e:
        app.logger.error(f"Erro na rota /deposit_pix: {e}")
        return jsonify({"error": f"Erro ao criar o pagamento Pix: {str(e)}"})

@app.route("/check_payment/<payment_id>")
@login_required
def check_payment(payment_id):
    try:
        payment = mp.payment().get(payment_id)["response"]
        if payment["status"] == "approved":
            amount = payment["transaction_amount"]
            with sqlite3.connect("database/triguinho.db") as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET balance = balance + ?, total_deposits_today = total_deposits_today + ? WHERE id = ?",
                          (amount, amount, current_user.id))
                log_transaction(current_user.id, "deposit_pix", amount)
                c.execute("SELECT balance FROM users WHERE id = ?", (current_user.id,))
                current_user.balance = c.fetchone()[0]
                conn.commit()
            app.logger.info(f"Pagamento Pix aprovado: ID {payment_id}, Valor: {amount}")
            return jsonify({"balance": current_user.balance, "message": f"Depósito de {amount} reais confirmado!"})
        return jsonify({"status": payment["status"]})
    except Exception as e:
        app.logger.error(f"Erro na rota /check_payment: {e}")
        return jsonify({"error": "Erro ao verificar o pagamento."})

@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    try:
        amount = float(request.form.get("amount", 0))
        if amount <= 0 or amount > current_user.balance:
            return jsonify({"error": "Valor inválido ou saldo insuficiente!"})
        if not current_user.pix_key:
            return jsonify({"error": "Chave Pix não cadastrada!"})

        with sqlite3.connect("database/triguinho.db") as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, current_user.id))
            log_transaction(current_user.id, "withdraw", -amount, f"Pix para {current_user.pix_key}")
            c.execute("SELECT balance FROM users WHERE id = ?", (current_user.id,))
            current_user.balance = c.fetchone()[0]
            conn.commit()

        app.logger.info(f"Saque solicitado: Valor: {amount}, Pix: {current_user.pix_key}, Saldo: {current_user.balance}")
        return jsonify({
            "balance": current_user.balance,
            "message": f"Saque de {amount} reais solicitado para a chave Pix {current_user.pix_key}. Transfira manualmente no Mercado Pago."
        })
    except Exception as e:
        app.logger.error(f"Erro na rota /withdraw: {e}")
        return jsonify({"error": "Erro ao processar o saque."})

@app.route("/admin")
@login_required
def admin():
    if current_user.username != "admin":
        flash("Acesso não autorizado.", "error")
        return redirect(url_for("index"))
    
    try:
        with sqlite3.connect("database/triguinho.db") as conn:
            c = conn.cursor()
            c.execute("SELECT balance, total_spins, total_payouts FROM banca WHERE id = 1")
            banca = c.fetchone()
            c.execute("SELECT username, balance, pix_key FROM users")
            users = c.fetchall()
            c.execute("SELECT user_id, type, amount, timestamp, result FROM transactions ORDER BY timestamp DESC LIMIT 50")
            transactions = c.fetchall()
        return render_template("admin.html", banca=banca, users=users, transactions=transactions)
    except Exception as e:
        app.logger.error(f"Erro na rota /admin: {e}")
        flash("Erro ao carregar o painel de administração.", "error")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)