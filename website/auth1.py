from flask import Blueprint, render_template, request, flash, redirect, url_for, session,get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User  
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.permanent = True
        email = request.form.get('email')
        password = request.form.get('password')  

        user = User.query.filter_by(email=email).first()
        if user:
            if user.rejected_at and (datetime.utcnow() - user.rejected_at).days < 7:
                flash('You are rejected. Try after a week or contact the librarian.', category='error')
                return redirect(url_for('auth.login'))
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
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')  
        roll_number = request.form.get('roll_number')  
        password = request.form.get('password')  
        email = request.form.get('email')
        confirm_password = request.form.get('confirmpassword') 
        phone_number = request.form.get('phone_number')  
        department = request.form.get('department')  
        year_of_graduation = request.form.get('year_of_graduation')  
        role = "Student"  

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(roll_number) != 7:
            flash('roll number must be 7 digits.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif password != confirm_password:
            flash('Passwords do not match.', category='error')
        elif len(phone_number) != 10:
            flash('phone number should be 10 digits.', category='error')
        else:
            new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'),
                            roll_number=roll_number, phone_number=phone_number, department=department,
                            year_of_graduation=year_of_graduation, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully.', category='success')
            return redirect(url_for('views.acc_created'))

    return render_template('signup.html')

@auth.route('/librariansignup', methods=['GET', 'POST'])
def librariansignup():
    if request.method == 'POST':
        name = request.form.get('name')  
        password = request.form.get('password') 
        email = request.form.get('email')
        confirm_password = request.form.get('confirmPassword') 
        phone_number = request.form.get('phone_number') 
        role = "Librarian"  

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif password != confirm_password:
            flash('Passwords do not match.', category='error')
        elif len(phone_number) != 10:
            flash('phone number should be 10 digits.', category='error')
        else:
            new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'),
                            phone_number=phone_number, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully.', category='success')
            return redirect(url_for('views.acc_created'))

    return render_template('librariansignup.html')

@auth.route('/logout')
@login_required
def logout():
    session.pop("USER", None)
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('views.home'))
