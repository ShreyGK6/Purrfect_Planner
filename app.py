from flask import Flask, render_template, flash, request, redirect, url_for


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

@app.route("/")
def home():
    return render_template("dashboard.html", user=MOCK_USER, pets=MOCK_PETS, tasks=MOCK_TASKS)

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")


        #need password authentication here (KEERTHIS PART)
        if username and password:
            flash(f"Welcome back, {username}!", 'success')
            return redirect(url_for("home"))
        else:
            flash("Invalid login.", "danger")
            return redirect(url_for("login.html"))


    return render_template("login.html")

@app.route("/add_task")
def add_task(): #set up ui for adding the tasks
    flash("add_task", "success")
    return render_template("base.html")

@app.route("/pet_profile")
def pet_profile():
    flash("pet_profile", "success")
    return render_template("base.html")


@app.route("/medical_records")
def medical_records():
    flash("medical_records", "success")
    return render_template("base.html")

@app.route("/register,", methods = ['POST', "GET"])
def register():
    if request.method == "POST":

        #validation logic -> KEERTHIS
        username = request.form.get("username")
        password = request.form.get('password')
        email = request.form.get("email")
        if not (username and email and password ):
            flash ("Please fill in all fields", "danger")
            return render_template("register.html")
        
        #SAVE TO DB - KEERTHIS
        flash("Account Successfully Created! Please Login.", 'success')
        return render_template("login.html")

    return render_template("register.html")








if __name__ == "__main__":
    app.run(debug=True)