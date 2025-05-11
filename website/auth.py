from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User  
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

auth = Blueprint('auth', __name__)

DEPARTMENTS = {
    "ECE": "ECE",
    "EEE": "EEE",
    "CSE": "CSE",
    "IMT": "IT",
    "ATE": "AUTO",
    "MCE": "MECH",
    "CVE": "CIVIL"
}
@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])  
def auth_page():
    if request.method == 'POST':
        print("Form submitted!")  # Debug statement
        action = request.form.get('action')
        if action == 'Login':
            return handle_login(request.form)
        elif action == 'Sign up':
            return handle_signup(request.form)

    return render_template("login.html", user=current_user)

def handle_login(form):
    session.permanent = True
    identifier = form.get('identifier')
    password = form.get('password')

    user = User.query.filter((User.email == identifier) | (User.roll_number == identifier)).first()
    if user:
        if user.rejected_at and (datetime.utcnow() - user.rejected_at).days < 7:
            flash('You are rejected. Try after a week or contact the librarian.', category='error')
            print('You are rejected. Try after a week or contact the librarian.')
            return redirect(url_for('auth.auth_page'))
        elif check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Your library account is being verified. Please await approval. Thank you!', category='error')
                print('Your library account is being verified. Please await approval. Thank you!')
            else:
                login_user(user, remember=True)
                session["USER"] = user.name
                return redirect(url_for('views.home'))
        else:
            flash('Incorrect password, try again.', category='error')
            print('Incorrect password, try again.')
    else:
        flash('Email (or) Roll Number does not exist.', category='error')
        print('Email (or) Roll Number does not exist.')
    
    return redirect(url_for('auth.auth_page'))

def handle_signup(form):
    role = form.get('role')
    name = form.get('name')
    password = form.get('password')
    mobile_number = form.get('mobile_number')
    email = form.get('email')
    confirm_password = form.get('confirm_password')
    
    # Determine if the user is a student or librarian
    if role == 'Librarian':
        roll_number = None  # Set roll number to None for librarian
        department = None
        year_of_graduation = None
    elif role == 'Student':
        roll_number = form.get('roll_number')
        
        # Validate roll number length only if role is Student
        if len(roll_number) not in [7, 8]:
            flash('Roll number must be 7 characters.', category='error')
            return redirect(url_for('auth.auth_page'))

        # Extract year and department from roll number
        year = int(roll_number[:2])
        department_code = roll_number[2:5]
        if len(roll_number) == 8:
            if roll_number[7] in ['L','T']:
                year_of_graduation = 2000 + year + 3
            else:
                flash('Invalid Roll Number (Enter in the Format 23EEE55T / 23EEE55L)', category='error')
            return redirect(url_for('auth.auth_page'))
                
        else:
            year_of_graduation = 2000 + year + 4  # Assuming roll number starts with the last two digits of the year
            department = DEPARTMENTS.get(department_code)

        if not department:
            flash('Invalid department code in roll number.', category='error')
            return redirect(url_for('auth.auth_page'))
    else:
        flash('Invalid role selection.', category='error')
        return redirect(url_for('auth.auth_page'))

    user = User.query.filter_by(email=email).first()
    if not (name and email and password and confirm_password):
        flash('All fields are required.', category='error')
        print('All fields are required.')
    elif user:
        flash('Email already exists.', category='error')
        print('Email already exists.')
    elif len(name) < 2:
        flash('First name must be greater than 1 character.', category='error')
        print('First name must be greater than 1 character.')
    elif len(email) < 4:
        flash('Email must be greater than 3 characters.', category='error')
        print('Email must be greater than 3 characters.')
    elif len(password) < 8:
        flash('Password must be at least 8 characters.', category='error')
        print('Password must be at least 8 characters.')
    elif password != confirm_password:
        flash('Passwords do not match.', category='error')
        print('Passwords do not match.')
    elif role not in ['Student', 'Librarian']:
        flash('Invalid role selection.', category='error')
        print('Invalid role selection.')

    else:
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'),mobilenumber=mobile_number,
                        roll_number=roll_number, department=department,
                        year_of_graduation=year_of_graduation, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully. You can login once you get verified', category='success')
        print('Account created successfully.')
        return redirect(url_for('auth.auth_page'))
    
    return redirect(url_for('auth.auth_page'))

@auth.route('/logout')
@login_required
def logout():
    session.pop("USER", None)
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('views.home'))
