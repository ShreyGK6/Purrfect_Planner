from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
import uuid
from Purrfect_Planner.config import Config
from Purrfect_Planner.models import db, User, Pet, Task, MedicalRecord

from datetime import datetime
from Purrfect_Planner.utils.notifications import notifications_bp

#loading environment variables from .env 
load_dotenv()



def create_app():
    #making flask app and point it to templates and static folders
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)  
    app.register_blueprint(notifications_bp)

    #uploads config - jerome code
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")  # absolute FS path
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB
    ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}

    def allowed_file(fname: str) -> bool:
        return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXT

    if not app.config.get("TESTING", False):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
            db_file = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
            folder = os.path.dirname(db_file)
            if folder:
                os.makedirs(folder, exist_ok=True)


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
                return redirect(url_for("login"))


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

    @app.route("/add_task", methods=['POST', 'GET'])
    @login_required
    def add_task(): #set up ui for adding the tasks
        #getting pets from db for current user
        my_pets = Pet.query.filter_by(owner_id=current_user.id).all() 
        pets = []
        for p in my_pets:
            pets.append(p.to_card())
        if request.method == "POST": #store all fields of data from frontend
            pet_id_raw = request.form.get("pet_id")
            title = (request.form.get("title") or "").strip()
            desc = (request.form.get("desc") or "").strip()
            date_str = request.form.get("date")
            repeat = request.form.get("repeat") or "None"
            #checking if required fields are there
            if not (pet_id_raw and title and date_str):
                flash("Pet, title, and date/time are required.", "danger")
                return render_template("add_task.html", pets=pets)
            try:
                pet_id = int(pet_id_raw)
            except ValueError:
                flash("Invalid pet selection.", "danger")
                return render_template("add_task.html", pets=pets)
            #making sure the pet belongs to the current user
            pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first()
            if not pet:
                flash("You cannot add tasks for that pet.", "danger")
                return render_template("add_task.html", pets=pets)
            #checking date format
            try:
                due_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Invalid date/time format.", "danger")
                return render_template("add_task.html", pets=pets)
            task = Task()                #creating empty task 
            task.pet_id = pet.id         #assigning values
            task.title = title
            task.desc = desc
            task.date = due_time
            task.repeat = repeat
            task.status = "pending"
            db.session.add(task)
            db.session.commit()
            flash("Task created successfully.", "success")
            return redirect(url_for("home"))
        return render_template("add_task.html", pets = pets) #make sure to pass in pets from db, using mock pets now
    
    @app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
    @login_required
    def edit_task(task_id):
        #only allowing editing tasks for pets owned by current user
        task = (Task.query.join(Pet).filter(Task.id == task_id, Pet.owner_id == current_user.id).first_or_404())
        my_pets = Pet.query.filter_by(owner_id=current_user.id).all()
        pets = []
        for p in my_pets:
            pets.append(p.to_card())
        if request.method == "POST":
            pet_id_raw = request.form.get("pet_id")
            title = (request.form.get("title") or "").strip()
            desc = (request.form.get("desc") or "").strip()
            date_str = request.form.get("date")
            repeat = request.form.get("repeat") or "None"
            #checking if required fields are there
            if not (pet_id_raw and title and date_str):
                flash("Pet, title, and date/time are required.", "danger")
                return render_template("edit_task.html", task=task, pets=pets)
            try:
                pet_id = int(pet_id_raw)
            except ValueError:
                flash("Invalid pet selection.", "danger")
                return render_template("edit_task.html", task=task, pets=pets)
            #making sure the pet belongs to the current user
            pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first()
            if not pet:
                flash("You cannot assign this task to that pet.", "danger")
                return render_template("edit_task.html", task=task, pets=pets)
            #checking date format
            try:
                due_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Invalid date/time format.", "danger")
                return render_template("edit_task.html", task=task, pets=pets)
            #Updating task parts and committing to db
            task.pet_id = pet.id
            task.title = title
            task.desc = desc
            task.date = due_time
            task.repeat = repeat
            db.session.commit()
            flash("Task updated successfully.", "success")
            return redirect(url_for("home"))
        return render_template("edit_task.html", task=task, pets=pets)
    
    @app.route("/delete_task/<int:task_id>", methods=["POST"])
    @login_required
    def delete_task(task_id):
        task = (Task.query.join(Pet).filter(Task.id == task_id, Pet.owner_id == current_user.id).first_or_404())
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.", "info")
        return redirect(request.referrer or url_for("home"))
    
    @app.route("/complete_task/<int:task_id>", methods=["POST"])
    @login_required
    def complete_task(task_id):
        task = (Task.query.join(Pet).filter(Task.id == task_id, Pet.owner_id == current_user.id).first_or_404())
        task.status = "completed"
        db.session.commit()
        flash("Task marked as complete.", "success")
        return redirect(request.referrer or url_for("home"))

    @app.route("/pet_profile/<int:pet_id>")
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
    
    @app.route("/records/<int:pet_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_med(pet_id):
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404() #curr pet belongs to curr user
        record = pet.medical_record #get exisitng record
        if request.method == "POST": #store all fields of data from frontend
            vaccine = (request.form.get("vaccine") or "").strip()
            allergies = (request.form.get("allergies") or "").strip()
            medication = (request.form.get("medication") or "").strip()
            vet_info = (request.form.get("vet_info") or "").strip()
            if record is None: #replace dummy record with newly created record if none exists. none exists by default
                record = MedicalRecord(
                    pet_id=pet.id,
                    vaccine=vaccine,
                    allergies=allergies,
                    medication=medication,
                    vet_info=vet_info,
                )
                db.session.add(record) #add to db and store it
            else: #if record already exists, update fields
                record.vaccine = vaccine
                record.allergies = allergies
                record.medication = medication
                record.vet_info = vet_info
            db.session.commit() #commit changes to db
            flash("Medical records updated!", "success") #success message
            return redirect(url_for("medical_records", pet_id=pet.id))

        #show exiting data
        if record:
            data = record.to_view()
        else: #show default blank fields (double check and hardcode again just in case)
            data = {"vaccine": "", "allergies": "", "medication": "", "vet_info": ""}

        return render_template("edit_med.html", pet=pet.to_card(), records=data)


    
    @app.route("/records/<int:pet_id>/clear", methods=["POST"])
    @login_required
    def delete_med(pet_id):
        pet = Pet.query.filter_by(id=pet_id, owner_id=current_user.id).first_or_404() #pet needs to belong to current user
        record = pet.medical_record
        #if record exists, clear all fields and commit to db "deleting it"
        #we do not want to delete the rows, just "clear" the data
        if record:
            record.vaccine = ""
            record.allergies = ""
            record.medication = ""
            record.vet_info = ""
            db.session.commit()
        flash("Medical Records Cleared!", "warning")
        return redirect(url_for("medical_records", pet_id=pet_id))
    
    
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
            # Commit to DB and redirect back to dashboard
            db.session.commit()
            flash("Pet updated successfully.", "success")
            return redirect(url_for("home"))
        # show the edit form with current data
        return render_template("edit_pet.html", pet=pet)
    
    #jerome code - delete pet
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
