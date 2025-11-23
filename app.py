from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import re
import os
import uuid  # for unique filenames

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="bhardwaj@123",
        database="user_crud"
    )

# ----------- READ -----------
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('index.html', users=users)

# ----------- CREATE -----------
@app.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        age = request.form.get('age')
        photo = request.files.get('photo')

        if not name or not email or not age:
            flash("All fields are required!", "danger")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format!", "danger")
        elif not age.isdigit() or int(age) <= 0:
            flash("Age must be a positive number!", "danger")
        else:
            filename = None
            if photo and photo.filename != "":
                ext = os.path.splitext(photo.filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png']:
                    flash("Only JPG, JPEG, PNG files are allowed!", "danger")
                    return render_template('add_user.html')
                filename = f"{uuid.uuid4().hex}{ext}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, age, photo) VALUES (%s, %s, %s, %s)",
                    (name, email, age, filename)
                )
                conn.commit()
                conn.close()
                flash("User added successfully!", "success")
                return redirect(url_for('index'))
            except mysql.connector.IntegrityError:
                flash("Email already exists!", "danger")

    return render_template('add_user.html')

# ----------- UPDATE -----------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cursor.fetchone()

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        age = request.form.get('age')
        photo = request.files.get('photo')

        if not name or not email or not age:
            flash("All fields are required!", "danger")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format!", "danger")
        elif not age.isdigit() or int(age) <= 0:
            flash("Age must be a positive number!", "danger")
        else:
            if photo and photo.filename != "":
                ext = os.path.splitext(photo.filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png']:
                    flash("Only JPG, JPEG, PNG files are allowed!", "danger")
                    return render_template('edit_user.html', user=user)

                # Delete old photo if exists
                if user['photo']:
                    old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], user['photo'])
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)

                filename = f"{uuid.uuid4().hex}{ext}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor.execute(
                    "UPDATE users SET name=%s, email=%s, age=%s, photo=%s WHERE id=%s",
                    (name, email, age, filename, id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET name=%s, email=%s, age=%s WHERE id=%s",
                    (name, email, age, id)
                )

            conn.commit()
            conn.close()
            flash("User updated successfully!", "success")
            return redirect(url_for('index'))

    conn.close()
    return render_template('edit_user.html', user=user)

# ----------- DELETE -----------
@app.route('/delete/<int:id>')
def delete_user(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT photo FROM users WHERE id=%s", (id,))
    photo = cursor.fetchone()
    if photo and photo[0]:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo[0])
        if os.path.exists(photo_path):
            os.remove(photo_path)

    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully!", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
