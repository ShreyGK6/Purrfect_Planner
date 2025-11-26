from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
import uuid
from config import Config
from models import db, User, Pet, Task, MedicalRecord

#loading environment variables from .env 
load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-key" #for flash messages only

#testing
MOCK_USER = {"username": "shivani"}

MOCK_PETS = [
    {"id": 1, "name": "Mochi", "type": "cat", "photo_path": "/static/img/placeholder_cat.png"},
    {"id": 2, "name": "Buddy", "type": "dog", "photo_path": "/static/img/placeholder_dog.png"},
    {"id": 3, "name": "Luna", "type": "cat", "photo_path": "/static/img/placeholder_cat.png"}
]

#need to include date with time
MOCK_TASKS = [
  {"id": 101, "pet_id": 1, "title": "Litter box clean",   "desc": "Scoop clumps and add fresh litter.", "date": "2025-11-06T20:00", "repeat": "daily",   "status": "pending"},
  {"id": 102, "pet_id": 1, "title": "Brush coat",         "desc": "Brush to reduce shedding.",          "date": "2025-11-08T17:00", "repeat": "weekly",  "status": "pending"},
  {"id": 103, "pet_id": 1, "title": "FVRCP booster check","desc": "Review vaccine record.",            "date": "2025-12-01T10:30", "repeat": "none",    "status": "pending"},
  {"id": 201, "pet_id": 2, "title": "Morning walk",       "desc": "30 min leash walk.",                "date": "2025-11-06T07:30", "repeat": "daily",   "status": "pending"},
  {"id": 202, "pet_id": 2, "title": "Heartworm preventive","desc":"Monthly chewable dose.",            "date": "2025-11-15T08:00", "repeat": "monthly", "status": "pending"},
  {"id": 203, "pet_id": 2, "title": "Bath + nail trim",   "desc": "Wash and trim nails.",              "date": "2025-11-10T14:00", "repeat": "monthly", "status": "pending"}
]

MOCK_RECORDS = {
    1: {"vaccine": "FVRCP, Rabies", "allergies": "None", "medication": "None", "vet_info": "UCR Vet Clinic"},
    2: {"vaccine": "DHPP, Rabies", "allergies": "Chicken", "medication": "Fish oil", "vet_info": "Riverside Vet"},
}

def create_app():
    #making flask app and point it to templates and static folders
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    #uploads config - jerome code
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")  # absolute FS path
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB
    ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}

    def allowed_file(fname: str) -> bool:
        return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXT

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    #making sure database foler exists for sqlite
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
            db_file = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_file), exist_ok=True)

    #connecting sqlalchemy to flask app.
    db.init_app(app)
    #helps flask manage user sessions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    #tells flask how to get a user object from the database whenever someone is logged in
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route("/")
    @login_required
    def home():
        pets = []
        for p in current_user.pets:
            pets.append(p.to_card())

        tasks = (
            Task.query.join(Pet)
            .filter(Pet.owner_id == current_user.id)
            .order_by(Task.date.asc())
            .all()
        )
        task_rows = []
        for t in tasks:
            task_rows.append(t.to_row())

        return render_template( "dashboard.html", user={"username": current_user.username}, pets=pets,tasks=task_rows )

    @app.route("/login", methods = ['POST', 'GET'])
    def login():
        if current_user.is_authenticated:
                return redirect(url_for("home"))
        
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first()


            #need password authentication here (KEERTHIS PART)
            if user and user.check_password(password):
                login_user(user)
                flash(f"Welcome back, {username}!", 'success')
                return redirect(url_for("home"))
            else:
                flash("Invalid login.", "danger")
                return redirect(url_for("login.html"))


        return render_template("login.html")

    @app.route("/logout")
    def logout():
        logout_user()
        flash("You’ve been logged out.", "info")
        return redirect(url_for("starter"))

    @app.route("/starter")
    def starter():
        if current_user.is_authenticated:
                return redirect(url_for("home"))
        return render_template("starter.html")
    
    # Add Pet - from jerome code
    @app.route("/add_pet", methods=["GET", "POST"])
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
    def add_task(): #set up ui for adding the tasks
        my_pets = Pet.query.filter_by(owner_id=current_user.id).all()
        pets = []
        for p in my_pets:
            pets.append(p.to_card())

        return render_template("add_task.html", pets = pets) #make sure to pass in pets from db, using mock pets now

    @app.route("/pet_profile<int:pet_id>")
    @login_required
    def pet_profile(pet_id):
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()
        pet_tasks = []
        for t in Task.query.filter_by(pet_id=pet.id).all():
            pet_tasks.append(t.to_row())

        if pet.medical_record:
            records = pet.medical_record.to_view()
        else:
            records = {"vaccine": "","allergies": "","medication": "","vet_info": "" }
        return render_template("pet_profile.html", pet=pet.to_card(), tasks=pet_tasks, records=records)


    @app.route("/records/<int:pet_id>")
    @login_required
    def medical_records(pet_id):
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404()
        if pet.medical_record:
            records = pet.medical_record.to_view()
        else:
             records = {"vaccine": "","allergies": "","medication": "","vet_info": "" }  

        return render_template("medical_records.html", pet=pet.to_card(), records=records)
    
    #jerome's code:
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

            # 6. Commit to DB and redirect back to dashboard
            db.session.commit()
            flash("Pet updated successfully.", "success")
            return redirect(url_for("home"))

        # GET: show the edit form with current data
        return render_template("edit_pet.html", pet=pet)

    @app.route("/register", methods = ['POST', "GET"])
    def register():
        if request.method == "POST":

            #validation logic -> KEERTHIS
            username = request.form.get("username")
            password = request.form.get('password')
            email = request.form.get("email")

            if not (username and email and password ):
                flash("All fields are required.", "danger")
                return render_template("register.html")
            #prevents duplicate usernames and emails
            if User.query.filter((User.username == username) | (User.email == email)).first():
                    flash("Username or email already exists.", "danger")
                    return render_template("register.html")
            #SAVE TO DB - KEERTHIS
            u = User(username=username, email=email)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("Account created successfully. Please log in.", "success")
            
            #SAVE TO DB - KEERTHIS
            return redirect(url_for("login"))  

        return render_template("register.html")
    
    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)