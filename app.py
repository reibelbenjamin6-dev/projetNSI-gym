import os
from flask import Flask, request, redirect, url_for, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Exercise, Performance

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
    return render_template("home.html") 

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

    return render_template("register.html")

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

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("home.html")

@app.route("/dashboard")
@login_required
def dashboard():

    exercises = Exercise.query.all()

    performances = Performance.query.filter_by(
        user_id=current_user.id
    ).all()

    total_points = 0

    for performance in performances:
        total_points = total_points + performance.points


    return render_template(
        "dashboard.html",
        exercises=exercises,
        performances=performances,
        total_points=total_points
    )


@app.route("/add-performance", methods=["GET", "POST"])
@login_required
def add_performance():
    exercises = Exercise.query.all()

    if request.method == "POST":
        exercise_id = request.form.get("exercise_id")
        weight = float(request.form.get("weight"))
        reps = int(request.form.get("reps"))

        points = weight * reps

        performance = Performance(
            weight=weight,
            reps=reps,
            points=points,
            user_id=current_user.id,
            exercise_id=exercise_id
        )

        db.session.add(performance)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_performance.html", exercises=exercises)

@app.route("/leaderboard")
@login_required
def leaderboard():
    leaderboard = []

    users = User.query.all()

    for user in users:
        total = 0

        for performance in user.performances:
            total = total + performance.points

        leaderboard.append({
            "username": user.username,
            "points": total
        })

    leaderboard.sort(
        key=lambda x: x["points"],
        reverse=True
    )

    return render_template("leaderboard.html", leaderboard=leaderboard)

@app.route("/exercise/<int:exercise_id>")
@login_required
def exercise_leaderboard(exercise_id):

    exercise = Exercise.query.get_or_404(exercise_id)

    leaderboard = []

    users = User.query.all()

    for user in users:

        total = 0

        for performance in user.performances:

            if performance.exercise_id == exercise.id:
                total = total + performance.points

        leaderboard.append({
            "username": user.username,
            "points": total
        })

    leaderboard.sort(
        key=lambda user: user["points"],
        reverse=True
    )

    return render_template(
        "exercise_leaderboard.html",
        leaderboard=leaderboard,
        exercise=exercise
    )

@app.route("/muscle/<muscle_name>")
@login_required
def muscle_leaderboard(muscle_name):
    leaderboard = []

    users = User.query.all()

    for user in users:
        total = 0

        for performance in user.performances:
            if performance.exercise.muscle == muscle_name:
                total = total + performance.points

        leaderboard.append({
            "username": user.username,
            "points": total
        })

    leaderboard.sort(
        key=lambda user: user["points"],
        reverse=True
    )

    return render_template(
        "muscle_leaderboard.html",
        leaderboard=leaderboard,
        muscle_name=muscle_name
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if Exercise.query.count() == 0:
            exercises = [
                Exercise(name="Bench Press", muscle="Chest"),
                Exercise(name="Curl", muscle="Biceps"),
                Exercise(name="Squat", muscle="Legs"),
                Exercise(name="Pull Up", muscle="Back")
            ]

            db.session.add_all(exercises)
            db.session.commit()

            print("Exercices ajoutés dans la base.")

    app.run(host="0.0.0.0", port=5000, debug=True)