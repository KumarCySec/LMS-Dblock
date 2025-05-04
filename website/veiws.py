from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from io import BytesIO
from sqlalchemy import func
from openpyxl import Workbook
from .models import User, Book, BorrowedBook, VolunteerAssignment, LibraryStatus
from . import db
from sqlalchemy.orm import joinedload
import logging

# Set up logger for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask Blueprint
views = Blueprint('views', __name__)

# Home/Dashboard route
@views.route('/home')
@views.route('/dashboard')
@login_required
def home():
    try:
        email = current_user.email
        user = User.query.filter_by(email=email).first()

        # Check if user exists
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('auth.logout'))

        # Fetch current library status
        library_status = LibraryStatus.query.first()
        is_library_open = library_status.is_open if library_status else True

        # Student Dashboard
        if user.role == "Student":
            naam = user.name
            user_id = user.id
            borrowed_books = BorrowedBook.query.filter_by(student_id=user_id).all()
            total_checked_out_books = len(borrowed_books)
            last_week = datetime.now() - timedelta(days=7)

            # Popular books in last 7 days
            popular_books = db.session.query(
                Book, func.count(BorrowedBook.id).label('borrow_count')
            ).join(BorrowedBook, Book.id == BorrowedBook.book_id) \
             .filter(BorrowedBook.borrowed_date >= last_week) \
             .group_by(Book.id) \
             .order_by(func.count(BorrowedBook.id).desc()).limit(4).all()

            # New arrivals in last 7 days
            new_arrivals = Book.query.filter(Book.added_at >= last_week) \
                                     .order_by(Book.added_at.desc()).limit(4).all()

            # Nearest due book info
            nearest_due_book = None
            days_until_next_due = None
            if borrowed_books:
                nearest_due_book = min(borrowed_books, key=lambda b: b.due_date)
                days_until_next_due = (nearest_due_book.due_date - datetime.now()).days

            # Fetch Today's Volunteer Assignment
            today_day = datetime.now().strftime("%A")
            today_assignment = VolunteerAssignment.query.filter_by(day=today_day).first()
            today_volunteers = []
            if today_assignment:
                today_volunteers = [today_assignment.volunteer1, today_assignment.volunteer2]

            logger.info("Student dashboard loaded successfully.")
            return render_template(
                'StuDashboard.html',
                naam=naam,
                new_arrivals=new_arrivals,
                popular_books=popular_books,
                nearest_due_book=nearest_due_book,
                total_checked_out_books=total_checked_out_books,
                days_until_next_due=days_until_next_due,
                library_status=is_library_open,
                today_volunteers=today_volunteers  # Pass today's volunteers to the template
            )


        # Librarian or Volunteer Dashboard
        elif user.role in ["Librarian", "Volunteer"]:
            naam = current_user.name
            today_day = datetime.now().strftime("%A")
            today_date = datetime.now().date()

            # Volunteer filtering
            all_volunteers = User.query.filter_by(role='Volunteer').all()
            DEPARTMENTS = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL", "AUTO"]
            selected_dept = request.args.get('department')
            sort_by = request.args.get('sort')

            # Department filtering
            if selected_dept:
                filtered_volunteers = [v for v in all_volunteers if v.department == selected_dept]
            else:
                filtered_volunteers = all_volunteers

            # Today's volunteer assignment
            assignment = VolunteerAssignment.query.options(joinedload(VolunteerAssignment.volunteer1),joinedload(VolunteerAssignment.volunteer2)).filter_by(day=today_day).first()
            if assignment:
                today_volunteers = [assignment.volunteer1, assignment.volunteer2]
            else:
                today_volunteers = []

            if assignment:
                print(f"[DEBUG] Assignment for {today_day}:")
                print(f" - Volunteer 1: {assignment.volunteer1.name if assignment.volunteer1 else 'None'}")
                print(f" - Volunteer 2: {assignment.volunteer2.name if assignment.volunteer2 else 'None'}")
            else:
                print(f"[DEBUG] No assignment found for {today_day}")


            # Borrowed books filtering and sorting
            borrowed_query = BorrowedBook.query.join(User, BorrowedBook.student_id == User.id)
            if selected_dept in DEPARTMENTS:
                borrowed_query = borrowed_query.filter(User.department == selected_dept)

            if sort_by == 'due_asc':
                borrowed_query = borrowed_query.order_by(BorrowedBook.due_date.asc())
            else:
                borrowed_query = borrowed_query.order_by(BorrowedBook.borrowed_date.desc())

            borrowed_books = borrowed_query.all()

            # Stats
            total_students = User.query.filter_by(role='Student').count()
            verified_students = User.query.filter_by(role='Student', is_verified=True).count()
            verified_volunteers = User.query.filter_by(role='Volunteer', is_verified=True).count()
            total_verified_users = verified_students+verified_volunteers
    
            pending_verifications = User.query.filter_by(role='Student', is_verified=False).count()
            total_volunteers = User.query.filter_by(role='Volunteer').count()
            total_available_books = Book.query.filter(Book.quantity > 0).count()
            total_checked_out_books = len(borrowed_books)

            last_week = datetime.now() - timedelta(days=7)
            new_arrivals = Book.query.filter(Book.added_at >= last_week)\
                                     .order_by(Book.added_at.desc()).limit(4).all()

            overdue_books_count = sum(
                1 for b in borrowed_books if b.due_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
            )

            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_assignment = {
                day: VolunteerAssignment.query.filter_by(day=day).first()
                for day in weekdays
            }

            logger.info("Librarian/Volunteer dashboard loaded successfully.")
            return render_template(
                'LibDashboard.html',
                naam=naam,
                total_students=total_students,
                verified_students=verified_students,
                pending_verifications=pending_verifications,
                new_arrivals=new_arrivals,
                total_volunteers=total_volunteers,
                total_verified_users=total_verified_users,
                total_available_books=total_available_books,
                total_checked_out_books=total_checked_out_books,
                borrowed_books=borrowed_books,
                overdue_books_count=overdue_books_count,
                today_volunteers=today_volunteers,
                departments=DEPARTMENTS,
                selected_department=selected_dept,
                selected_sort=sort_by,
                library_status=is_library_open,
                current_date=today_date,
                weekly_assignment=weekly_assignment,
                weekdays=weekdays,
                volunteers=all_volunteers,
                today=today_day
            )

        # Admin dashboard
        elif user.role == "Admin":
            return render_template('MADashboard.html', naam=user.name)

        else:
            return render_template('error.html', error_message='User role not recognized.')

    except Exception as e:
        logger.error(f"[ERROR] Exception in home(): {e}")
        return render_template('error.html', error_message='Something went wrong!')


# Route to export checkout register to Excel
@views.route('/export-checkout-register-excel')
@login_required
def export_checkout_register_excel():
    if current_user.role != "Librarian":
        return render_template('error.html', error_message="Unauthorized")

    borrowed_books = BorrowedBook.query.all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Checkout Register"
    ws.append(["Student Name", "Roll No.", "Department", "Book Title", "Borrow Date", "Due Date"])

    for entry in borrowed_books:
        ws.append([
            entry.student.name,
            getattr(entry.student, 'roll_no', 'N/A'),
            getattr(entry.student, 'department', 'N/A'),
            entry.book.title,
            entry.borrowed_date.strftime('%d-%m-%Y'),
            entry.due_date.strftime('%d-%m-%Y')
        ])

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    logger.info("Checkout register exported successfully.")
    return send_file(file_stream, download_name="Checkout_Register.xlsx", as_attachment=True)


# Toggle library open/close status
@views.route('/toggle-library-status', methods=['POST'])
@login_required
def toggle_library_status():
    if current_user.role not in ['Librarian', 'Volunteer', 'Admin']:
        return render_template('error.html', error_message="Unauthorized")

    library_status = LibraryStatus.query.first()
    if library_status:
        library_status.is_open = not library_status.is_open
    else:
        library_status = LibraryStatus(is_open=True)
        db.session.add(library_status)

    db.session.commit()
    flash('Library status updated!', 'success')
    logger.info(f"Library status toggled to {'open' if library_status.is_open else 'closed'}.")
    return redirect(url_for('views.home'))


# Assign weekly volunteers to a day
@views.route('/assign-weekly-volunteers', methods=['POST'])
@login_required
def assign_weekly_volunteers():
    if current_user.role != 'Volunteer':
        return render_template('error.html', error_message="Unauthorized access")

    try:
        selected_day = request.form.get('selected_day')
        department = request.form.get('department')
        volunteer1_id = request.form.get('volunteer1_id')
        volunteer2_id = request.form.get('volunteer2_id')

        if not all([selected_day, volunteer1_id, volunteer2_id]):
            flash("All fields are required.", "warning")
            return redirect(url_for('views.home'))

        # Validate day
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if selected_day not in weekdays:
            flash("Invalid day selected.", "danger")
            return redirect(url_for('views.home'))

        # Compute the exact date of the selected day
        today = datetime.now().date()
        today_index = today.weekday()
        target_index = weekdays.index(selected_day)
        days_ahead = (target_index - today_index + 7) % 7
        selected_date = today + timedelta(days=days_ahead)

        # Validate volunteer IDs
        volunteer1 = User.query.filter_by(id=volunteer1_id, department=department).first()
        volunteer2 = User.query.filter_by(id=volunteer2_id, department=department).first()

        if not volunteer1 or not volunteer2:
            flash("Invalid volunteers selected or volunteers do not belong to the selected department.", "danger")
            return redirect(url_for('views.home'))

        # Create or update assignment
        assignment = VolunteerAssignment.query.filter_by(day=selected_day).first()
        if assignment:
            assignment.volunteer1_id = volunteer1.id
            assignment.volunteer2_id = volunteer2.id
        else:
            assignment = VolunteerAssignment(
                day=selected_day,
                volunteer1_id=volunteer1.id,
                volunteer2_id=volunteer2.id
            )
            db.session.add(assignment)

        db.session.commit()
        logger.info(f"Assigned volunteers for {selected_day}: {volunteer1.name}, {volunteer2.name}")
        flash(f"Volunteers assigned for {selected_day} ({selected_date.strftime('%d-%b-%Y')})", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(f"[ERROR] Volunteer assignment failed: {e}")
        flash("Failed to assign volunteers. Please try again.", "danger")

    return redirect(url_for('views.home'))


# Settings route
@views.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Placeholder for future settings handling
        return redirect(url_for('settings'))
    return render_template('Settings.html')
