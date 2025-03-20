from flask import Blueprint,render_template,request,session, url_for, redirect,flash, current_app
from flask_login import login_required,current_user
from .models import Book,BorrowedBook,User
from datetime import datetime,timedelta,timezone
from . import db
from sqlalchemy import or_
import os
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

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
    
    if request.method == 'POST':
        # Update user details
        user.name = request.form.get('name')
        user.roll_number = request.form.get('roll_number')
        user.phone_number = request.form.get('phone_number')
        user.department = request.form.get('department')
        user.year_of_graduation = request.form.get('year_of_graduation')

        # Handle profile picture
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    user.profile_picture_url = url_for('static', filename=f'uploads/pfp/{filename}')
                except RequestEntityTooLarge:
                    flash('File is too large. Maximum size is 2 MB.', 'error')
                    return redirect(request.url)
                except Exception as e:
                    flash(f'An error occurred: {str(e)}', 'error')
                    return redirect(request.url)
            else:
                flash('Invalid file type. Only jpg, jpeg, and png files are allowed.', 'error')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('stu.profile'))

    return render_template('Profile.html', user=user)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}
