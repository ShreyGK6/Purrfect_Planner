import os
import uuid

from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from config import Config
from models import db, User, Pet, Task, MedicalRecord

load_dotenv()

def create_app():
    # app + config
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    #uploads config 
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")  # absolute FS path
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB
    ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}

    def allowed_file(fname: str) -> bool:
        return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXT

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        db_file = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

    # db + login
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------- Routes ----------

    @app.route("/starter")
    def starter():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        return render_template("starter.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
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
            else:
                flash("Invalid login.", "danger")
                return redirect(url_for("login"))

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You’ve been logged out.", "info")
        return redirect(url_for("starter"))

    # Dashboard 
    @app.route("/")
    @login_required
    def home():
        # Pets for current user
        pets = [p.to_card() for p in current_user.pets]

        # Upcoming tasks for current user 
        tasks = (
            Task.query.join(Pet)
            .filter(Pet.owner_id == current_user.id)
            .order_by(Task.date.asc())
            .all()
        )
        task_rows = [t.to_row() for t in tasks]

        return render_template(
            "dashboard.html",
            user={"username": current_user.username},
            pets=pets,
            tasks=task_rows,
        )

    # link to /dashboard 
    @app.route("/dashboard")
    @login_required
    def dashboard_alias():
        return home()

    # Add Pet 
    @app.route("/add-pet", methods=["GET", "POST"])
    @login_required
    def add_pet():
        if request.method == "GET":
            return render_template("add_pet.html")

        name = (request.form.get("name") or "").strip()
        species = (request.form.get("species") or "").strip()
        photo = request.files.get("photo")

        if not name or not species:
            flash("Name and species are required!", "danger")
            return redirect(url_for("add_pet"))

        filename = None
        if photo and photo.filename:
            if not allowed_file(photo.filename):
                flash("Invalid file type. Please upload PNG/JPG/GIF.", "danger")
                return redirect(url_for("add_pet"))
            safe = secure_filename(photo.filename)
            root, ext = os.path.splitext(safe)
            unique = f"{root}_{uuid.uuid4().hex[:8]}{ext}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique)
            photo.save(save_path)
            # store web path for templates:
            filename = f"/static/uploads/{unique}"

        pet = Pet(name=name, type=species, photo_path=filename or "", owner_id=current_user.id)
        db.session.add(pet)
        db.session.commit()

        flash("Pet added successfully!", "success")
        return redirect(url_for("home"))

    @app.route("/add_task")
    @login_required
    def add_task():
        my_pets = Pet.query.filter_by(owner_id=current_user.id).all()
        pets = [p.to_card() for p in my_pets]
        return render_template("add_task.html", pets=pets)

    @app.route("/pet_profile/<int:pet_id>")
    @login_required
    def pet_profile(pet_id):
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()
        pet_tasks = [t.to_row() for t in Task.query.filter_by(pet_id=pet.id).all()]
        records = pet.medical_record.to_view() if pet.medical_record else {
            "vaccine": "", "allergies": "", "medication": "", "vet_info": ""
        }
        return render_template("pet_profile.html", pet=pet.to_card(), tasks=pet_tasks, records=records)

    @app.route("/records/<int:pet_id>")
    @login_required
    def medical_records(pet_id):
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()
        records = pet.medical_record.to_view() if pet.medical_record else {
            "vaccine": "", "allergies": "", "medication": "", "vet_info": ""
        }
        return render_template("medical_records.html", pet=pet.to_card(), records=records)

    @app.route("/register", methods=["GET", "POST"])
    def register():
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

            u = User(username=username, email=email)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
