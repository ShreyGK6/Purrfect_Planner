from flask import Flask, render_template, flash, request, redirect, url_for, session


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

@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("starter"))
    return render_template("dashboard.html", user=MOCK_USER, pets=MOCK_PETS, tasks=MOCK_TASKS)

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")


        #need password authentication here (KEERTHIS PART)
        if username and password:
            flash(f"Welcome back, {username}!", 'success')
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for("home"))
        else:
            flash("Invalid login.", "danger")
            return redirect(url_for("login.html"))


    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("username", None)
    return redirect(url_for("starter"))

@app.route("/starter")
def starter():
    return render_template("starter.html")

@app.route("/add_task")
def add_task(): #set up ui for adding the tasks
    return render_template("add_task.html", pets = MOCK_PETS) #make sure to pass in pets from db, using mock pets now

@app.route("/pet_profile<int:pet_id>")
def pet_profile(pet_id):
    pet = None
    for p  in MOCK_PETS: #need to connect db to this
        if p.get("id") == pet_id: #for every pet, get its id and save pet as "pet"
            pet = p
            break
    pet_tasks =[]
    for t in MOCK_TASKS:
        if t.get("pet_id") == pet_id: #get all tasks for certain pet
            pet_tasks.append(t)
    

    records = MOCK_RECORDS.get(pet_id, {"vaccine": "", "allergies": "", "medication": "", "vet_info": ""})

    
    return render_template("pet_profile.html", pet=pet, tasks=pet_tasks, records=records)


@app.route("/records/<int:pet_id>")
def medical_records(pet_id):
    pet = None
    for p  in MOCK_PETS: #need to connect db to this
        if p.get("id") == pet_id: #for every pet, get its id and save pet as "pet"
            pet = p
            break
    
    records = MOCK_RECORDS.get(pet_id, {"vaccine": "", "allergies": "", "medication": "", "vet_info": ""})  

    return render_template("medical_records.html", pet=pet, records=records)

@app.route("/register", methods = ['POST', "GET"])
def register():
    if request.method == "POST":

        #validation logic -> KEERTHIS
        username = request.form.get("username")
        password = request.form.get('password')
        email = request.form.get("email")
        if not (username and email and password ):
            return render_template("register.html")
        
        #SAVE TO DB - KEERTHIS
        return redirect(url_for("login"))  

    return render_template("register.html")








if __name__ == "__main__":
    app.run(debug=True)