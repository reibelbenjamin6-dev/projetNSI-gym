import os
from flask import Flask, request, redirect, url_for, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Exercise, Performance

RANKS = [
    (0, "Bronze"),
    (500, "Argent"),
    (1250, "Or"),
    (2500, "Platine"),
    (5000, "Diamant"),
    (8000, "Titan"),
    (12000, "Colosse"),
    (17000, "Alpha"),
    (23000, "Noel Deyzel"),
    (30000, "Anatoly"),
    (38000, "GigaChad"),
    (47000, "Larry Wheels 2x8"),
    (57000, "Tren Twins"),
    (70000, "Sam Sulek"),
    (85000, "Lee Heath"),
    (105000, "David Laid"),
    (130000, "Jay Cutler"),
    (160000, "Tom Platz"),
    (200000, "Cbum"),
    (250000, "Arnold"),
    (325000, "Ronnie Mode"),
    (425000, "Lightweight Baby"),
    (550000, "Mr Olympia"),
    (700000, "IFBB Elite"),
    (900000, "Abdelkader"),
    (1200000, "Olympia Legend"),
    (1500000, "Greek Physique"),
]

def get_rank(points):
    current_rank = "Bronze"

    for minimum_points, rank_name in RANKS:
        if points >= minimum_points:
            current_rank = rank_name

    return current_rank

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



def get_next_rank(points):
    for minimum_points, rank_name in RANKS:
        if points < minimum_points:
            points_needed = minimum_points - points
            return rank_name, points_needed

    return "Rank maximum atteint", 0

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

    user_rank = get_rank(total_points)
    next_rank, points_needed = get_next_rank(total_points)

    next_rank_threshold = total_points + points_needed

    if next_rank_threshold == 0:
        rank_progress = 100
    else:
        rank_progress = round((total_points / next_rank_threshold) * 100, 1)

    return render_template(
        "dashboard.html",
        exercises=exercises,
        performances=performances,
        total_points=total_points,
        user_rank=user_rank,
        next_rank=next_rank,
        points_needed=points_needed,
        rank_progress=rank_progress
    )


@app.route("/add-performance")
@login_required
def choose_muscle():
    muscles = []

    exercises = Exercise.query.all()

    for exercise in exercises:
        if exercise.muscle not in muscles:
            muscles.append(exercise.muscle)

    return render_template("choose_muscle.html", muscles=muscles)
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
    "points": total,
    "rank": get_rank(total)
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
    "points": total,
    "rank": get_rank(total)
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
            "points": total,
            "rank": get_rank(total)
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

@app.route("/add-performance/<muscle_name>", methods=["GET", "POST"])
@login_required
def add_performance_by_muscle(muscle_name):
    exercises = Exercise.query.filter_by(muscle=muscle_name).all()

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

    return render_template(
        "add_performance.html",
        exercises=exercises,
        muscle_name=muscle_name
    )


@app.route("/exercises/<muscle_name>")
@login_required
def exercises_by_muscle(muscle_name):
    exercises = Exercise.query.filter_by(muscle=muscle_name).all()

    return render_template(
        "exercises_by_muscle.html",
        exercises=exercises,
        muscle_name=muscle_name
    )

@app.route("/delete-performance/<int:performance_id>", methods=["POST"])
@login_required
def delete_performance(performance_id):
    performance = Performance.query.get_or_404(performance_id)

    if performance.user_id != current_user.id:
        return redirect(url_for("dashboard"))

    db.session.delete(performance)
    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/ranks")
@login_required
def ranks_page():
    return render_template("ranks.html", ranks=RANKS)


@app.route("/best-scores")
@login_required
def best_scores():
    scores = []

    users = User.query.all()

    for user in users:
        total = 0

        for performance in user.performances:
            total = total + performance.points

        scores.append({
            "username": user.username,
            "points": total,
            "rank": get_rank(total)
        })

    scores.sort(
        key=lambda user: user["points"],
        reverse=True
    )

    return render_template("best_scores.html", scores=scores)

@app.route("/profile")
@login_required
def profile():
    performances = Performance.query.filter_by(
        user_id=current_user.id
    ).all()

    total_points = 0
    exercise_scores = {}
    muscle_scores = {}
    personal_records = {}

    for performance in performances:
        total_points = total_points + performance.points

        exercise_name = performance.exercise.name
        muscle_name = performance.exercise.muscle

        if exercise_name not in exercise_scores:
            exercise_scores[exercise_name] = 0

        exercise_scores[exercise_name] = exercise_scores[exercise_name] + performance.points

        if muscle_name not in muscle_scores:
            muscle_scores[muscle_name] = 0

        muscle_scores[muscle_name] = muscle_scores[muscle_name] + performance.points

        if exercise_name not in personal_records:
            personal_records[exercise_name] = performance
        else:
            if performance.points > personal_records[exercise_name].points:
                personal_records[exercise_name] = performance

    best_exercise = None
    best_exercise_points = 0

    for exercise_name in exercise_scores:
        if exercise_scores[exercise_name] > best_exercise_points:
            best_exercise = exercise_name
            best_exercise_points = exercise_scores[exercise_name]

    best_muscle = None
    best_muscle_points = 0

    for muscle_name in muscle_scores:
        if muscle_scores[muscle_name] > best_muscle_points:
            best_muscle = muscle_name
            best_muscle_points = muscle_scores[muscle_name]

    user_rank = get_rank(total_points)
    next_rank, points_needed = get_next_rank(total_points)

    return render_template(
        "profile.html",
        performances=performances,
        total_points=total_points,
        user_rank=user_rank,
        next_rank=next_rank,
        points_needed=points_needed,
        exercise_scores=exercise_scores,
        muscle_scores=muscle_scores,
        personal_records=personal_records,
        best_exercise=best_exercise,
        best_exercise_points=best_exercise_points,
        best_muscle=best_muscle,
        best_muscle_points=best_muscle_points
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if Exercise.query.count() == 0:
            exercises = [

    # CHEST
    Exercise(name="Bench Press", muscle="Chest"),
    Exercise(name="Incline Bench Press", muscle="Chest"),
    Exercise(name="Decline Bench Press", muscle="Chest"),
    Exercise(name="Dumbbell Press", muscle="Chest"),
    Exercise(name="Incline Dumbbell Press", muscle="Chest"),
    Exercise(name="Chest Fly", muscle="Chest"),
    Exercise(name="Cable Fly", muscle="Chest"),
    Exercise(name="Push Up", muscle="Chest"),
    Exercise(name="Dips", muscle="Chest"),
    Exercise(name="Machine Chest Press", muscle="Chest"),

    # BACK
    Exercise(name="Pull Up", muscle="Back"),
    Exercise(name="Chin Up", muscle="Back"),
    Exercise(name="Lat Pulldown", muscle="Back"),
    Exercise(name="Barbell Row", muscle="Back"),
    Exercise(name="Dumbbell Row", muscle="Back"),
    Exercise(name="T-Bar Row", muscle="Back"),
    Exercise(name="Deadlift", muscle="Back"),
    Exercise(name="Seated Cable Row", muscle="Back"),
    Exercise(name="Rack Pull", muscle="Back"),
    Exercise(name="Straight Arm Pulldown", muscle="Back"),

    # SHOULDERS
    Exercise(name="Shoulder Press", muscle="Shoulders"),
    Exercise(name="Arnold Press", muscle="Shoulders"),
    Exercise(name="Lateral Raise", muscle="Shoulders"),
    Exercise(name="Front Raise", muscle="Shoulders"),
    Exercise(name="Rear Delt Fly", muscle="Shoulders"),
    Exercise(name="Machine Shoulder Press", muscle="Shoulders"),
    Exercise(name="Cable Lateral Raise", muscle="Shoulders"),
    Exercise(name="Face Pull", muscle="Shoulders"),
    Exercise(name="Upright Row", muscle="Shoulders"),
    Exercise(name="Dumbbell Press", muscle="Shoulders"),

    # BICEPS
    Exercise(name="Barbell Curl", muscle="Biceps"),
    Exercise(name="Dumbbell Curl", muscle="Biceps"),
    Exercise(name="Hammer Curl", muscle="Biceps"),
    Exercise(name="Preacher Curl", muscle="Biceps"),
    Exercise(name="Cable Curl", muscle="Biceps"),
    Exercise(name="Spider Curl", muscle="Biceps"),
    Exercise(name="EZ Bar Curl", muscle="Biceps"),
    Exercise(name="Concentration Curl", muscle="Biceps"),
    Exercise(name="Incline Curl", muscle="Biceps"),
    Exercise(name="Machine Curl", muscle="Biceps"),

    # TRICEPS
    Exercise(name="Tricep Pushdown", muscle="Triceps"),
    Exercise(name="Skull Crusher", muscle="Triceps"),
    Exercise(name="Overhead Extension", muscle="Triceps"),
    Exercise(name="Close Grip Bench", muscle="Triceps"),
    Exercise(name="Bench Dips", muscle="Triceps"),
    Exercise(name="Cable Pushdown", muscle="Triceps"),
    Exercise(name="Single Arm Pushdown", muscle="Triceps"),
    Exercise(name="French Press", muscle="Triceps"),
    Exercise(name="JM Press", muscle="Triceps"),
    Exercise(name="Machine Tricep Extension", muscle="Triceps"),

    # LEGS
    Exercise(name="Squat", muscle="Legs"),
    Exercise(name="Front Squat", muscle="Legs"),
    Exercise(name="Hack Squat", muscle="Legs"),
    Exercise(name="Leg Press", muscle="Legs"),
    Exercise(name="Romanian Deadlift", muscle="Legs"),
    Exercise(name="Bulgarian Split Squat", muscle="Legs"),
    Exercise(name="Lunges", muscle="Legs"),
    Exercise(name="Leg Extension", muscle="Legs"),
    Exercise(name="Leg Curl", muscle="Legs"),
    Exercise(name="Smith Machine Squat", muscle="Legs"),

    # ABS
    Exercise(name="Crunch", muscle="Abs"),
    Exercise(name="Cable Crunch", muscle="Abs"),
    Exercise(name="Leg Raise", muscle="Abs"),
    Exercise(name="Hanging Leg Raise", muscle="Abs"),
    Exercise(name="Sit Up", muscle="Abs"),
    Exercise(name="Russian Twist", muscle="Abs"),
    Exercise(name="Plank", muscle="Abs"),
    Exercise(name="Ab Wheel", muscle="Abs"),
    Exercise(name="Toe Touch", muscle="Abs"),
    Exercise(name="Mountain Climbers", muscle="Abs"),

    # FOREARMS
    Exercise(name="Wrist Curl", muscle="Forearms"),
    Exercise(name="Reverse Wrist Curl", muscle="Forearms"),
    Exercise(name="Farmer Walk", muscle="Forearms"),
    Exercise(name="Dead Hang", muscle="Forearms"),
    Exercise(name="Grip Trainer", muscle="Forearms"),
    Exercise(name="Plate Pinch", muscle="Forearms"),
    Exercise(name="Hammer Hold", muscle="Forearms"),
    Exercise(name="Behind Back Curl", muscle="Forearms"),
    Exercise(name="Finger Curl", muscle="Forearms"),
    Exercise(name="Towel Pull Up", muscle="Forearms"),

    # CALVES
    Exercise(name="Standing Calf Raise", muscle="Calves"),
    Exercise(name="Seated Calf Raise", muscle="Calves"),
    Exercise(name="Donkey Calf Raise", muscle="Calves"),
    Exercise(name="Single Leg Calf Raise", muscle="Calves"),
    Exercise(name="Smith Machine Calf Raise", muscle="Calves"),
    Exercise(name="Leg Press Calf Raise", muscle="Calves"),
    Exercise(name="Jump Rope", muscle="Calves"),
    Exercise(name="Box Jump", muscle="Calves"),
    Exercise(name="Farmer Walk On Toes", muscle="Calves"),
    Exercise(name="Machine Calf Raise", muscle="Calves"),
]

            db.session.add_all(exercises)
            db.session.commit()

            print("Exercices ajoutés dans la base.")

    app.run(host="0.0.0.0", port=5000, debug=True)