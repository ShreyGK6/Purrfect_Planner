import os
import uuid
from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from config import Config
from models import db, User, Pet, Task, MedicalRecord
from utils.notifications import notifications_bp

load_dotenv()

# ------------------ CONFIG ------------------

USE_MOCK = False 

# ------------------ MOCK DATA (for UI testing) ------------------

MOCK_USER = {"username": "shivani"}
MOCK_PETS = [
    {"id": 1, "name": "Mochi", "type": "cat", "photo_path": "/static/img/placeholder_cat.png"},
    {"id": 2, "name": "Buddy", "type": "dog", "photo_path": "/static/img/placeholder_dog.png"},
    {"id": 3, "name": "Luna", "type": "cat", "photo_path": "/static/img/placeholder_cat.png"},
]

MOCK_TASKS = [
    {"id": 101, "pet_id": 1, "title": "Litter box clean", "desc": "Scoop clumps and add fresh litter.", "date": "2025-11-06T20:00", "repeat": "daily", "status": "pending"},
    {"id": 102, "pet_id": 1, "title": "Brush coat", "desc": "Brush to reduce shedding.", "date": "2025-11-08T17:00", "repeat": "weekly", "status": "pending"},
    {"id": 201, "pet_id": 2, "title": "Morning walk", "desc": "30 min leash walk.", "date": "2025-11-06T07:30", "repeat": "daily", "status": "pending"},
]

MOCK_RECORDS = {
    1: {"vaccine": "FVRCP, Rabies", "allergies": "None", "medication": "None", "vet_info": "UCR Vet Clinic"},
    2: {"vaccine": "DHPP, Rabies", "allergies": "Chicken", "medication": "Fish oil", "vet_info": "Riverside Vet"},
}


# ------------------ APP FACTORY ------------------

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.secret_key = "dev-key"

    # Register blueprint (your notifications)
    app.register_blueprint(notifications_bp)

    # Uploads
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Database setup
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ------------------ ROUTES ------------------

    @app.route("/starter")
    def starter():
        if not USE_MOCK and current_user.is_authenticated:
            return redirect(url_for("home"))
        return render_template("starter.html")

    # ---------- LOGIN ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if USE_MOCK:
            if request.method == "POST":
                username = request.form.get("username")
                password = request.form.get("password")
                if username and password:
                    session["logged_in"] = True
                    session["username"] = username
                    flash(f"Welcome back, {username}!", "success")
                    return redirect(url_for("home"))
                flash("Invalid login.", "danger")
            return render_template("login.html")

        # Real login
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for("home"))
            flash("Invalid login.", "danger")

        return render_template("login.html")

    # ---------- LOGOUT ----------
    @app.route("/logout")
    def logout():
        if USE_MOCK:
            session.clear()
            return redirect(url_for("starter"))
        logout_user()
        flash("You’ve been logged out.", "info")
        return redirect(url_for("starter"))

    # ---------- DASHBOARD ----------
    @app.route("/")
    def home():
        if USE_MOCK:
            if not session.get("logged_in"):
                return redirect(url_for("starter"))
            return render_template("dashboard.html", user=MOCK_USER, pets=MOCK_PETS, tasks=MOCK_TASKS)

        # Real DB version
        if not current_user.is_authenticated:
            return redirect(url_for("starter"))
        pets = [p.to_card() for p in current_user.pets]
        tasks = (
            Task.query.join(Pet)
            .filter(Pet.owner_id == current_user.id)
            .order_by(Task.date.asc())
            .all()
        )
        return render_template("dashboard.html", user={"username": current_user.username}, pets=pets, tasks=[t.to_row() for t in tasks])

    # ---------- ADD PET ----------
    @app.route("/add-pet", methods=["GET", "POST"])
    def add_pet():
        if USE_MOCK:
            return render_template("add_pet.html", pets=MOCK_PETS)
        # (Jerome’s add_pet logic here if USE_MOCK=False)
        return render_template("add_pet.html")

    # ---------- ADD TASK ----------
    @app.route("/add_task")
    def add_task():
        if USE_MOCK:
            return render_template("add_task.html", pets=MOCK_PETS)
        my_pets = Pet.query.filter_by(owner_id=current_user.id).all()
        return render_template("add_task.html", pets=[p.to_card() for p in my_pets])

    # ---------- PET PROFILE ----------
    @app.route("/pet_profile/<int:pet_id>")
    def pet_profile(pet_id):
        if USE_MOCK:
            pet = next((p for p in MOCK_PETS if p["id"] == pet_id), None)
            tasks = [t for t in MOCK_TASKS if t["pet_id"] == pet_id]
            records = MOCK_RECORDS.get(pet_id, {"vaccine": "", "allergies": "", "medication": "", "vet_info": ""})
            return render_template("pet_profile.html", pet=pet, tasks=tasks, records=records)

        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()
        pet_tasks = [t.to_row() for t in Task.query.filter_by(pet_id=pet.id).all()]
        records = pet.medical_record.to_view() if pet.medical_record else {"vaccine": "", "allergies": "", "medication": "", "vet_info": ""}
        return render_template("pet_profile.html", pet=pet.to_card(), tasks=pet_tasks, records=records)

    # ---------- MEDICAL RECORDS ----------
    @app.route("/records/<int:pet_id>")
    def medical_records(pet_id):
        if USE_MOCK:
            pet = next((p for p in MOCK_PETS if p["id"] == pet_id), None)
            records = MOCK_RECORDS.get(pet_id, {"vaccine": "", "allergies": "", "medication": "", "vet_info": ""})
            return render_template("medical_records.html", pet=pet, records=records)

        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()
        records = pet.medical_record.to_view() if pet.medical_record else {"vaccine": "", "allergies": "", "medication": "", "vet_info": ""}
        return render_template("medical_records.html", pet=pet.to_card(), records=records)

    # ---------- REGISTER ----------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if USE_MOCK:
            if request.method == "POST":
                username = request.form.get("username")
                password = request.form.get("password")
                email = request.form.get("email")
                if not (username and password and email):
                    flash("All fields are required.", "danger")
                    return render_template("register.html")
                flash("Mock registration complete!", "success")
                return redirect(url_for("login"))
            return render_template("register.html")

        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")

            if not (username and email and password):
                flash("All fields are required.", "danger")
                return render_template("register.html")

            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash("Username or email already exists.", "danger")
                return render_template("register.html")

            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        if not USE_MOCK:
            db.create_all()
    app.run(debug=True)