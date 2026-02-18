import os
from flask import Flask, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-change-me"

os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return "<h1>Accueil</h1><p><a href='/register'>Register</a> | <a href='/login'>Login</a></p>"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")

        if len(username) < 3 or len(password) < 6:
            return "Pseudo>=3 et mdp>=6. <a href='/register'>Retour</a>"

        if User.query.filter_by(username=username).first():
            return "Pseudo déjà pris. <a href='/register'>Retour</a>"

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))

    return """
    <h1>Inscription</h1>
    <form method="post">
      <input name="username" placeholder="Pseudo" required>
      <input name="password" type="password" placeholder="Mot de passe" required>
      <button type="submit">Créer</button>
    </form>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        return "Identifiants incorrects. <a href='/login'>Réessayer</a>"

    return """
    <h1>Connexion</h1>
    <form method="post">
      <input name="username" placeholder="Pseudo" required>
      <input name="password" type="password" placeholder="Mot de passe" required>
      <button type="submit">Se connecter</button>
    </form>
    """

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    return f"<h1>Dashboard</h1><p>Connecté: {current_user.username}</p><p><a href='/logout'>Logout</a></p>"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
