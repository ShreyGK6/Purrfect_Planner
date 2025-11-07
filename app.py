from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os
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
            records = {
                "vaccine": "",
                "allergies": "",
                "medication": "",
                "vet_info": ""
            }
        
        records = {"vaccine": "","allergies": "","medication": "","vet_info": "" }  

        return render_template("medical_records.html", pet=pet.to_card(), records=records)

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