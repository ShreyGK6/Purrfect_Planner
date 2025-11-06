import os
from flask import Flask, render_template
from config import Config
from models import db

# function that creates the app
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # making sure database folder exists
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        db_file = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

    #connecting the database to the flask app
    db.init_app(app)

    @app.route("/")
    def index():
        return "Backend bootstrapped"

    return app

if __name__ == "__main__":
    app = create_app()
    #creating the database
    with app.app_context():
        db.create_all()
    app.run(debug=True)
