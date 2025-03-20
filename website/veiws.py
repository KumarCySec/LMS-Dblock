from flask import Blueprint,render_template,request,session, url_for, redirect, flash
from flask_login import login_required,current_user
from .models import User,Book,BorrowedBook
from datetime import datetime,timezone,timedelta
from sqlalchemy import func
from website import db

views = Blueprint('views', __name__)

@views.route('/acc_created', methods=['GET','POST'])
def acc_created():
    return render_template('acc_created.html')

@views.route('/home')
@views.route('/dashboard')
@login_required
def home():
    try:
        if current_user.is_authenticated:
            email = current_user.email
            user = User.query.filter_by(email=email).first()

            if user.role == "Student":
                naam = user.name
                user_id = user.id

                # Query the borrowed books for the student
                borrowed_books = BorrowedBook.query.filter_by(student_id=user_id).all()

                # Calculate total number of checked out books
                total_checked_out_books = len(borrowed_books)

                # Calculate last week's date
                last_week = datetime.now() - timedelta(days=7)

                # Query to find popular books based on borrow count
                popular_books = db.session.query(Book,func.count(BorrowedBook.id).label('borrow_count')).join(BorrowedBook, Book.id == BorrowedBook.book_id).filter(BorrowedBook.borrowed_date >= last_week).group_by(Book.id).order_by(func.count(BorrowedBook.id).desc()).limit(4).all()

                # New Arrival
                last_week = datetime.now() - timedelta(days=7)
                new_arrivals = Book.query.filter(Book.added_at >= last_week).order_by(Book.added_at.desc()).limit(4).all()

                # Find the nearest due book
                nearest_due_book = None
                days_until_next_due = None

                if borrowed_books:
                    # Find the nearest due book
                    nearest_due_book = min(borrowed_books, key=lambda book: book.due_date)

                    # Calculate days until next due
                    now = datetime.now()
                    days_until_next_due = (nearest_due_book.due_date - now).days
                return render_template('StuDashboard.html', naam=naam,new_arrivals=new_arrivals, popular_books=popular_books, nearest_due_book=nearest_due_book, total_checked_out_books=total_checked_out_books,
                           days_until_next_due=days_until_next_due) # user="kumar"
            
            elif user.role == "Librarian" or user.role == "Volunteer":
                try:
                    if current_user.is_authenticated and (current_user.role == "Librarian" or current_user.role == "Volunteer"):
                        naam = current_user.name

                        total_students = User.query.filter(User.role=='Student').count()
                        verified_students = User.query.filter(User.role=='Student', User.is_verified==True).count()
                        pending_verifications = User.query.filter(User.role=='Student', User.is_verified==False).count()
                        total_volunteers = User.query.filter(User.role=='Volunteer').count()

                        total_available_books = Book.query.filter(Book.quantity > 0).count()

                        # Query all borrowed books
                        borrowed_books = BorrowedBook.query.all()

                        # Calculate total number of checked out books by all students
                        total_checked_out_books = len(borrowed_books)

                        # New Arrival
                        last_week = datetime.now() - timedelta(days=7)
                        new_arrivals = Book.query.filter(Book.added_at >= last_week).order_by(Book.added_at.desc()).limit(4).all()

                        # Calculate books that are not returned after the due date
                        overdue_books_count = 0
                        today = datetime.now(timezone.utc)

                        for borrowed_book in borrowed_books:
                            if borrowed_book.due_date.replace(tzinfo=timezone.utc) < today:
                                overdue_books_count += 1

                        return render_template('LibDashboard.html', naam=naam, total_students=total_students, verified_students=verified_students,
                                            pending_verifications=pending_verifications,new_arrivals=new_arrivals, total_volunteers=total_volunteers, total_available_books=total_available_books,
                                            total_checked_out_books=total_checked_out_books, borrowed_books=borrowed_books, overdue_books_count=overdue_books_count)
                    else:
                        return render_template('error.html', error_message='Unauthorized access')  # Display error for unauthorized access

                except Exception as e:
                    # Log the exception for debugging
                    print(f"Exception occurred: {e}")
                    return render_template('error.html', error_message='An error occurred')  # Display generic error message
            
            elif user.role == "Admin":
                naam = current_user.name
                return render_template('MADashboard.html', naam=naam)
            
            else:
                return render_template('error.html', error_message='User not found')  # Display appropriate error message
        else:
            return redirect(url_for('auth.logout'))
            return render_template('error.html', error_message='User not authenticated')  # Display appropriate error message

    except Exception as e:
        # Log the exception for debugging
        print(f"Exception occurred: {e}")
        return render_template('error.html', error_message='An error occurred')  # Display generic error message


@views.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        return redirect(url_for('settings'))

    return render_template('Settings.html')

