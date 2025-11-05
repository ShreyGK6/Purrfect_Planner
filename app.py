import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'dev-key-change-me'

# File upload settings
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dummy data (for testing before backend connection)
pets = []

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', pets=pets)

@app.route('/add-pet', methods=['GET', 'POST'])
def add_pet():
    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        photo = request.files.get('photo')

        if not name or not species:
            flash('Name and species are required!', 'danger')
            return redirect(url_for('add_pet'))
        
        filename = None
        if photo and photo.filename:
            if not allowed_file(photo.filename):
                flash('Invalid file type. Upload PNG/JPG/GIF.', 'danger')
                return redirect(url_for('add_pet'))
            safe = secure_filename(photo.filename)
            root, ext = os.path.splitext(safe)
            unique = f"{root}_{uuid.uuid4().hex[:8]}{ext}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            photo.save(save_path)
            filename = unique


        pet = {'name': name, 'species': species, 'photo': filename}
        pets.append(pet)
        flash('Pet added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_pet.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
