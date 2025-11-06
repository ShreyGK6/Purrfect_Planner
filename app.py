from flask import Flask, render_template, flash, request, redirect, url_for


app = Flask(__name__)
app.secret_key = "dev-key" #for flash messages only

@app.route("/")
def home():
    flash("home", "success")
    return render_template("base.html")

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
def add_task():
    flash("add_task", "success")
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