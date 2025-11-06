from flask import Flask, render_template, flash


app = Flask(__name__)
app.secret_key = "dev-key" #for flash messages only

@app.route("/")
def home():
    flash("home", "success")
    return render_template("base.html")

@app.route("/login")
def login():
    flash("login", "success")
    return render_template("base.html")

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