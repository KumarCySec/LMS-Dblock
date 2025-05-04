from flask import Blueprint,render_template,request,session, url_for, redirect,flash, current_app
from flask_login import login_required,current_user
from .models import Book,BorrowedBook,User
from datetime import datetime,timedelta,timezone
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from sqlalchemy import or_
import os
import logging
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

logger = logging.getLogger(__name__)

stu = Blueprint('stu', __name__)

@stu.route('/viewbooks', methods=['GET','POST'])
@login_required
def ViewBooks():
    search_query = request.args.get('search', '')
    lang_filter = request.args.get('language', '')
    
    page = request.args.get('page', 1, type=int)  # Default to page 1 if not specified

    # Base query to fetch books
    query = Book.query

    # Apply search filter
    if search_query:
        query = query.filter(or_(Book.title.ilike(f'%{search_query}%'), Book.author.ilike(f'%{search_query}%')))

    # Fetch distinct languages for filter dropdown
    languages = db.session.query(Book.language.distinct().label("language")).all()
    unique_languages = [lang.language for lang in languages]

    # Pagination
    books = query.paginate(page=page, per_page=9)  # Adjust per_page as needed

    return render_template('SViewBooks.html', books=books, search_query=search_query, lang_filter=lang_filter, unique_languages=unique_languages)

@stu.route('/checkoutbooks', methods=['GET', 'POST'])
@login_required
def CheckoutBooks():
    search_query = request.args.get('search_query', '')  # Get search query from URL parameter

    if request.method == 'POST':
        # Handle form submission for checkout
        book_ids = request.form.getlist('book_ids')  # Get list of selected book IDs from form

        if not book_ids:
            flash('Please select at least one book to checkout.', 'error')
            print('Please select at least one book to checkout.', 'error')
            return redirect(url_for('stu.CheckoutBooks'))

        try:
            for book_id in book_ids:
                book = Book.query.get(book_id)
                if book and book.quantity > 0:
                    # Decrease quantity of available books
                    book.quantity -= 1

                    due_date = datetime.now(timezone.utc) + timedelta(days=14)
                    
                    # Record the borrowing transaction in BorrowedBook table
                    borrowed_book = BorrowedBook(
                        student_id=current_user.id,
                        book_id=book_id,
                        borrowed_date=datetime.now(timezone.utc),
                        due_date=due_date,
                        is_verified=False  # Initial status is not verified
                    )
                    db.session.add(borrowed_book)

            db.session.commit()
            flash('Books checked out successfully. Please wait for verification.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error checking out books: {str(e)}', 'error')

        return redirect(url_for('stu.CheckoutBooks'))

    # Fetch all available books for checkout (with optional search filtering)
    if search_query:
        books = Book.query.filter(
            (Book.title.ilike(f'%{search_query}%')) |
            (Book.author.ilike(f'%{search_query}%')) |
            (Book.isbn.ilike(f'%{search_query}%'))
        ).filter(Book.quantity > 0).all()
    else:
        books = Book.query.filter(Book.quantity > 0).all()

    return render_template('CheckoutBooks.html', books=books, search_query=search_query)

@stu.route('/mybooks', methods=['GET', 'POST'])
@login_required
def MyBooks():
    if request.method == 'POST':
        if 'return_book_id' in request.form:
            # Handle returning a book
            return_book_id = int(request.form['return_book_id'])
            borrowed_book = BorrowedBook.query.get(return_book_id)

            if borrowed_book and borrowed_book.student_id == current_user.id:
                # Update book quantity and delete the borrowed book record
                book = borrowed_book.book
                book.quantity += 1
                db.session.delete(borrowed_book)
                db.session.commit()
                flash(f'Book "{book.title}" returned successfully.', 'success')
                return redirect(url_for('stu.MyBooks'))

        elif 'renew_book_id' in request.form:
            # Handle renewing a book
            renew_book_id = int(request.form['renew_book_id'])
            borrowed_book = BorrowedBook.query.get(renew_book_id)

            if borrowed_book:
                # Calculate new due date (e.g., extend by 14 days)
                new_due_date = datetime.utcnow() + timedelta(days=14)
                borrowed_book.due_date = new_due_date
                db.session.commit()
                flash(f'Book "{borrowed_book.book.title}" renewed successfully.', 'success')
                return redirect(url_for('stu.MyBooks'))

    # Fetch all borrowed books for the current user
    borrowed_books = BorrowedBook.query.filter_by(student_id=current_user.id).all()

    return render_template('MyBooks.html', borrowed_books=borrowed_books)

@stu.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(current_user.id)

    if not user:
        flash("User not found. Please login again.", "danger")
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        try:
            # ----------------------------
            # 🔄 PROFILE DETAILS UPDATE
            # ----------------------------
            if form_type == 'profile_update':
                name = request.form.get('name', '').strip()
                phone = request.form.get('phone', '').strip()
                department = request.form.get('department', '').strip()
                year = request.form.get('year_of_graduation', '').strip()

                # Basic validation
                if not name:
                    flash("Name cannot be empty.", "warning")
                    return redirect(url_for('stu.profile'))

                if year and not year.isdigit():
                    flash("Graduation year must be a number.", "warning")
                    return redirect(url_for('stu.profile'))

                # Update fields
                user.name = name
                user.phone_number = phone
                user.department = department
                user.year_of_graduation = int(year) if year else None

                db.session.commit()

                logger.info(f"[INFO] User '{user.email}' updated profile.")
                flash("Profile updated successfully!", "success")
                return redirect(url_for('stu.profile'))

            # ----------------------------
            # 🔐 PASSWORD RESET
            # ----------------------------
            elif form_type == 'password_reset':
                current_pwd = request.form.get('current_password')
                new_pwd = request.form.get('new_password')
                confirm_pwd = request.form.get('confirm_password')

                # Check current password
                if not check_password_hash(user.password, current_pwd):
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for('stu.profile'))

                # Validate new passwords
                if new_pwd != confirm_pwd:
                    flash("New passwords do not match.", "warning")
                    return redirect(url_for('stu.profile'))

                if len(new_pwd) < 6:
                    flash("New password must be at least 6 characters.", "warning")
                    return redirect(url_for('stu.profile'))

                # Hash and save new password
                user.password = generate_password_hash(new_pwd, method='pbkdf2:sha256')
                db.session.commit()

                logger.info(f"[INFO] User '{user.email}' successfully reset their password.")
                flash("Password updated successfully!", "success")
                return redirect(url_for('stu.profile'))

            else:
                logger.warning(f"[WARNING] Unknown form type submitted by {user.email}: {form_type}")
                flash("Invalid form submitted.", "danger")
                return redirect(url_for('stu.profile'))

        except Exception as e:
            logger.exception(f"[ERROR] Failed to process profile update for {user.email}: {str(e)}")
            flash("Something went wrong. Please try again later.", "danger")
            return redirect(url_for('stu.profile'))

    # GET request — show profile page
    return render_template("Profile.html", user=user)