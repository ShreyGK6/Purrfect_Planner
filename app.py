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


@app.route("/register")
def register():
    flash("register", "success")
    return render_template("base.html")








if __name__ == "__main__":
    app.run(debug=True)