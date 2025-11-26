import os
import uuid
from datetime import datetime   

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

    @app.route("/add_task", methods=["GET", "POST"])
    @login_required
    def add_task():
        if request.method == "POST":
            # Read and clean form data
            pet_id = request.form.get("pet_id", type=int)
            title = (request.form.get("title") or "").strip()
            desc = (request.form.get("desc") or "").strip()
            date_str = (request.form.get("date") or "").strip()
            repeat = (request.form.get("repeat") or "None").strip()

            # Basic validation
            if not pet_id or not title or not date_str:
                flash("Pet, task title, and date/time are required.", "danger")
                return redirect(url_for("add_task"))

            # Ensure the pet belongs to the current user
            pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first()
            if not pet:
                flash("Invalid pet selected.", "danger")
                return redirect(url_for("add_task"))

            try:
                when = datetime.fromisoformat(date_str)
            except ValueError:
                flash("Invalid date/time format.", "danger")
                return redirect(url_for("add_task"))

            # Create and save the task
            task = Task(
                pet_id=pet.id,
                title=title,
                desc=desc,
                date=when,
                repeat=repeat,
            )
            db.session.add(task)
            db.session.commit()

            flash("Task created!", "success")
         
            return redirect(url_for("home"))

        my_pets = Pet.query.filter_by(owner_id=current_user.id).all()
        pets = [p.to_card() for p in my_pets]
        return render_template("add_task.html", pets=pets)

    @app.route("/tasks/<int:task_id>/complete", methods=["POST"])
    @login_required
    def complete_task(task_id):
        task = (
            Task.query.join(Pet)
            .filter(Task.id == task_id, Pet.owner_id == current_user.id)
            .first_or_404()
        )

        task.status = "completed"
        db.session.commit()
        flash("Task marked as completed.", "success")

        next_url = request.referrer or url_for("home")
        return redirect(next_url)


    @app.route("/tasks/<int:task_id>/delete", methods=["POST"])
    @login_required
    def delete_task(task_id):
        task = (
            Task.query.join(Pet)
            .filter(Task.id == task_id, Pet.owner_id == current_user.id)
            .first_or_404()
        )

        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.", "success")

        next_url = request.referrer or url_for("home")
        return redirect(next_url)


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
        
    @app.route("/pets/<int:pet_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_pet(pet_id):
        # Make sure the pet belongs to the logged-in user
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()

        if request.method == "POST":
            # Read form data
            name = (request.form.get("name") or "").strip()
            species = (request.form.get("species") or "").strip()
            file = request.files.get("photo")

            # Validate basic fields
            if not name or not species:
                flash("Name and species are required.", "danger")
                return redirect(url_for("edit_pet", pet_id=pet.id))

            # Update text fields
            pet.name = name
            pet.type = species

            # handle new photo upload
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Invalid file type. Upload PNG/JPG/GIF.", "danger")
                    return redirect(url_for("edit_pet", pet_id=pet.id))

                safe = secure_filename(file.filename)
                root, ext = os.path.splitext(safe)
                unique = f"{root}_{uuid.uuid4().hex[:8]}{ext}"
                upload_dir = app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, unique)
                file.save(save_path)

                # try to delete the old file (only if it was in /static/uploads)
                if pet.photo_path and pet.photo_path.startswith("/static/uploads/"):
                    old_fs_path = pet.photo_path.lstrip("/")  
                    try:
                        os.remove(old_fs_path)
                    except OSError:
                        # If the file is missing ignore the error
                        pass

                # Store the new web path
                pet.photo_path = f"/static/uploads/{unique}"

            db.session.commit()
            flash("Pet updated successfully.", "success")
            return redirect(url_for("home"))

        # show the edit form with current data
        return render_template("edit_pet.html", pet=pet)

    @app.route("/pets/<int:pet_id>/delete", methods=["POST"])
    @login_required
    def delete_pet(pet_id):
        # Make sures the pet belongs to the logged in user
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()

        if pet.photo_path and pet.photo_path.startswith("/static/uploads/"):
            old_fs_path = pet.photo_path.lstrip("/")  
            try:
                os.remove(old_fs_path)
            except OSError:
                pass

        db.session.delete(pet)
        db.session.commit()

        flash("Pet deleted successfully (and related tasks/records were removed).", "success")
        return redirect(url_for("home"))


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
