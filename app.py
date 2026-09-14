from flask import Flask
from database import init_db
from routes.admin import admin_bp
from routes.operador import operador_bp

app = Flask(__name__)
app.secret_key = 'chave_secreta_cnc_system'

# Registra os módulos (Blueprints) do sistema
app.register_blueprint(admin_bp)
app.register_blueprint(operador_bp)

# Inicializa o banco de dados na inicialização
init_db()

if __name__ == '__main__':
    app.run(debug=True)