from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_, distinct
from datetime import datetime, timedelta,date
from .models import Book, User, Donor,BorrowedBook, VolunteerAssignment
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from .forms import CSRFProtectForm

logger = logging.getLogger(__name__)
lib = Blueprint('lib', __name__)

def role_required_volunteer_librarian():
    """Restrict access to volunteers and librarian only."""
    if current_user.role.lower() not in ["volunteer", "librarian"]:
        flash("Unauthorized access.", "danger")
        logger.warning(f"[SECURITY] Unauthorized access attempt by {current_user.email}")
        return redirect(url_for("views.home"))
    
@lib.route('/addbooks', methods=['GET', 'POST'])
@login_required
def AddBooks():
    role_required_volunteer_librarian()
    donors = Donor.query.all()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        published_date = datetime.strptime(request.form['published_date'], '%Y-%m-%d') if request.form['published_date'] else None
        quantity = int(request.form['quantity'])
        language = request.form['language']
        donor_name = request.form['donor_name']
        date_of_donation = datetime.strptime(request.form['date_of_donation'], '%Y-%m-%d') if request.form['date_of_donation'] else None

        if len(title) < 2:
            flash('Title must be greater than 1 character.', category='error')
        elif len(author) < 2:
            flash('Author name must be greater than 1 character.', category='error')
        elif quantity < 0:
            flash('Quantity cannot be negative.', category='error')
        else:
            try:
                if donor_name == 'new_donor':
                    donor = Donor(
                        name=request.form['new_donor_name'],
                        department=request.form['donor_department'],
                        year_of_graduation=request.form['donor_yog']
                    )
                    db.session.add(donor)
                    db.session.commit()
                    donor_id = donor.id
                else:
                    donor = Donor.query.filter_by(name=donor_name).first()
                    donor_id = donor.id if donor else None
                
                added_at = datetime.utcnow()

                book = Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    published_date=published_date,
                    quantity=quantity,
                    language=language,
                    date_of_donation=date_of_donation,
                    donor_id=donor_id,
                    added_at=added_at
                )
                db.session.add(book)
                db.session.commit()
                flash('Book added successfully.', 'success')
                return redirect(url_for('lib.AddBooks'))
            except Exception as e:
                flash(f'Error adding book: {str(e)}', 'error')
                db.session.rollback()

    return render_template('AddBooks.html', donors=donors)

@lib.route('/viewbooks', methods=['GET', 'POST'])
@login_required
def ViewBooks():
    role_required_volunteer_librarian()
    unique_languages = db.session.query(Book.language).distinct().all()
    unique_languages = [lang[0] for lang in unique_languages]  # Extracting from tuples
    search_query = request.args.get('search', '')
    lang_filter = request.args.get('language', '')
    page = request.args.get('page', 1, type=int)

    query = Book.query
    if search_query:
        query = query.filter(or_(Book.title.ilike(f'%{search_query}%'), Book.author.ilike(f'%{search_query}%')))
    if lang_filter:
        query = query.filter(Book.language == lang_filter)

    books = query.paginate(page=page, per_page=9)

    return render_template('ViewBooks.html', books=books, search_query=search_query, lang_filter=lang_filter, unique_languages=unique_languages )

@lib.route('/editbooks', methods=['GET', 'POST'])
@login_required
def EditBooks():
    role_required_volunteer_librarian()
    if request.method == 'POST':
        action = request.form.get('action')
        book_id = int(request.form.get('book_id'))

        try:
            book = Book.query.get(book_id)

            if action == 'edit':
                book.title = request.form.get('title')
                book.author = request.form.get('author')
                book.language = request.form.get('language')
                book.quantity = int(request.form.get('quantity'))

                published_date_str = request.form.get('published_date')
                book.published_date = datetime.strptime(published_date_str, '%Y-%m-%d').date() if published_date_str else None

                donor_id = request.form.get('donor')
                book.donor_id = int(donor_id) if donor_id else None

                donation_date_str = request.form.get('donation_date')
                book.date_of_donation = datetime.strptime(donation_date_str, '%Y-%m-%d').date() if donation_date_str else None

                db.session.commit()
                flash('Book details updated successfully.', 'success')
            elif action == 'delete':
                db.session.delete(book)
                db.session.commit()
                flash('Book deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error updating book: {str(e)}', 'error')
            db.session.rollback()

    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '')

    query = Book.query
    if search_query:
        query = query.filter(or_(Book.title.ilike(f"%{search_query}%"), Book.author.ilike(f"%{search_query}%")))

    books = query.paginate(page=page, per_page=per_page)
    donors = Donor.query.all()

    return render_template('EditBooks.html', books=books, donors=donors, search_query=search_query)

@lib.route('/viewstudentsdetails', methods=['GET', 'POST'])
@login_required
def ViewStudentsDetails():
    role_required_volunteer_librarian()
    search_query = request.args.get('search', '')
    students = User.query.filter(User.role == 'Student').filter(
        or_(User.name.ilike(f'%{search_query}%'), User.roll_number.ilike(f'%{search_query}%'))
    ).all() if search_query else User.query.filter_by(role='Student').all()

    return render_template('ViewStudents.html', students=students, search_query=search_query)

@lib.route('/editstudentsdetails', methods=['GET', 'POST'])
@login_required
def EditStudentsDetails():
    role_required_volunteer_librarian()
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            student_id = request.form.get('student_id')
            student = User.query.get(student_id)

            if not student:
                flash("Student not found.", "error")
                return redirect(url_for('lib.EditStudentsDetails'))

            if action == 'edit':
                student.name = request.form.get('name')
                student.roll_number = request.form.get('roll_number')
                student.email = request.form.get('email')
                student.phone_number = request.form.get('phone_number')
                student.department = request.form.get('department')
                student.year_of_graduation = request.form.get('year_of_graduation')

                db.session.commit()
                flash('✅ Student details updated successfully.', 'success')
                print(f"🟢 [DEBUG] Updated Student ID: {student_id} - {student.name}")

            elif action == 'delete':
                db.session.delete(student)
                db.session.commit()
                flash('❌ Student deleted successfully.', 'success')
                print(f"🟢 [DEBUG] Deleted Student ID: {student_id} - {student.name}")

        # Handling GET request (Search, Filter, Pagination)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        search_query = request.args.get('search', '').strip()
        dept_filter = request.args.get('dept', '')

        query = User.query.filter_by(role='Student')

        if search_query:
            query = query.filter(
                User.name.ilike(f"%{search_query}%") | 
                User.roll_number.ilike(f"%{search_query}%")
            )
            print(f"🟢 [DEBUG] Search Query: {search_query}")

        if dept_filter:
            query = query.filter(User.department == dept_filter)
            print(f"🟢 [DEBUG] Department Filter: {dept_filter}")

        query = query.order_by(User.name.asc())
        students = query.paginate(page=page, per_page=per_page)
        print(f"🟢 [DEBUG] Total Students Found: {students.total}")

        return render_template(
            'EditStudents.html',
            students=students.items,
            pagination=students,  # The correct pagination object
            search_query=search_query,
            dept_filter=dept_filter
        )

    except Exception as e:
        flash(f"🚨 Error: {str(e)}", "error")
        print(f"🔴 [ERROR] {str(e)}")
        return redirect(url_for('lib.EditStudentsDetails'))



@lib.route('/adddonor', methods=['GET', 'POST'])
@login_required
def AddDonor():
    role_required_volunteer_librarian()
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('dept')
        year_of_graduation = request.form.get('yog')
        mobile_number = request.form.get('mobilenumber')
        email = request.form.get('email')
        address = request.form.get('address')

        if not name or not department or not year_of_graduation:
            flash('Name, department, and year of graduation are mandatory fields.', 'error')
            return redirect(url_for('lib.AddDonor'))

        try:
            new_donor = Donor(
                name=name,
                department=department,
                                year_of_graduation=year_of_graduation,
                mobilenumber=mobile_number,
                email=email,
                address=address
            )

            db.session.add(new_donor)
            db.session.commit()
            flash('Donor added successfully.', 'success')
            return redirect(url_for('lib.AddDonor'))
        except Exception as e:
            flash(f'Error adding donor: {str(e)}', 'error')
            db.session.rollback()

    return render_template('AddDonor.html')

@lib.route('/viewdonors')
@login_required
def ViewDonors():
    role_required_volunteer_librarian()
    search_query = request.args.get('search', '')
    dept_filter = request.args.get('dept', '')
    sort_order = request.args.get('sort', '')

    query = Donor.query
    if search_query:
        query = query.filter(Donor.name.ilike(f'%{search_query}%'))
    if dept_filter:
        query = query.filter(Donor.department == dept_filter)
    if sort_order == 'asc':
        query = query.order_by(Donor.year_of_graduation.asc())
    elif sort_order == 'desc':
        query = query.order_by(Donor.year_of_graduation.desc())

    donors = query.all()

    return render_template('ViewDonors.html', donors=donors, search_query=search_query, dept_filter=dept_filter, sort_order=sort_order)

@lib.route('/editdonors', methods=['GET', 'POST'])
@login_required
def EditDonors():
    role_required_volunteer_librarian()
    if request.method == 'POST':
        donor_id = request.form.get('donor_id')
        donor = Donor.query.get(donor_id)

        try:
            if request.form.get('action') == 'edit':
                donor.name = request.form.get('name')
                donor.department = request.form.get('dept')
                donor.year_of_graduation = request.form.get('yog')
                donor.mobilenumber = request.form.get('mobilenumber')
                donor.email = request.form.get('email')
                donor.address = request.form.get('address')
                db.session.commit()
                flash('Donor details updated successfully!', 'success')

            elif request.form.get('action') == 'delete':
                books = Book.query.filter_by(donor_id=donor.id).all()
                for book in books:
                    book.donor_id = None
                db.session.delete(donor)
                db.session.commit()
                flash('Donor deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error updating/deleting donor: {str(e)}', 'error')
            db.session.rollback()

        return redirect(url_for('lib.EditDonors'))

    search_query = request.args.get('search', '')
    dept_filter = request.args.get('dept', '')
    sort_order = request.args.get('sort', '')

    query = Donor.query
    if search_query:
        query = query.filter(Donor.name.ilike(f'%{search_query}%'))
    if dept_filter:
        query = query.filter(Donor.department == dept_filter)
    if sort_order == 'asc':
        query = query.order_by(Donor.year_of_graduation.asc())
    elif sort_order == 'desc':
        query = query.order_by(Donor.year_of_graduation.desc())

    donors = query.all()

    return render_template('EditDonors.html', donors=donors, search_query=search_query, dept_filter=dept_filter, sort_order=sort_order)

@lib.route('/managestudents', methods=['GET', 'POST'])
@login_required
def manage_students():
    role_required_volunteer_librarian()
    verified_students = User.query.filter(User.is_verified == True, User.role.in_(['Student', 'Volunteer'])).all()
    unverified_students = User.query.filter(User.is_verified == False, User.role.in_(['Student', 'Volunteer']), User.rejected_at == None).all()
    rejected_students = User.query.filter(User.rejected_at != None).all()  # Fetching rejected students
    csrf_form = CSRFProtectForm()

    if request.method == 'POST':
        if csrf_form.validate_on_submit():
            student_id = request.form.get('student_id')
            action = request.form.get('action')

            student = User.query.get(student_id)
            if student:
                try:
                    if action == 'verify':
                        student.is_verified = True
                        db.session.commit()
                        flash(f'{student.name} has been verified successfully!', category='success')
                    elif action == 'promote_to_volunteer':
                        student.role = 'Volunteer'
                        db.session.commit()
                        flash(f'{student.name} has been promoted to Volunteer!', category='success')
                    elif action == 'depromote_to_student':
                        student.role = 'Student'
                        db.session.commit()
                        flash(f'{student.name} has been depromoted to Student!', category='success')
                    elif action == 'deverify':
                        student.is_verified = False
                        db.session.commit()
                        flash(f'{student.name} has been deverified!', category='success')
                    elif action == 'reject':
                        student.rejected_at = datetime.utcnow()
                        db.session.commit()
                        flash(f'{student.name} has been rejected!', category='success')
                    elif action == 'delete':
                        db.session.delete(student)
                        db.session.commit()
                        flash(f'{student.name} has been deleted successfully!', category='success')
                    elif action == 'delete_all_rejected':
                        rejected_students = User.query.filter(User.rejected_at != None).all()
                        for rejected_student in rejected_students:
                            db.session.delete(rejected_student)
                        db.session.commit()
                        flash('All rejected students have been deleted successfully!', category='success')
                except Exception as e:
                    flash(f'Error performing action: {str(e)}', category='error')
                    db.session.rollback()
            else:
                flash('Student not found!', category='error')

        return redirect(url_for('lib.manage_students'))

    return render_template('ManageStudents.html', verified_students=verified_students, unverified_students=unverified_students, rejected_students=rejected_students, form=csrf_form)

@lib.route('/manage_checkouts', methods=['POST','GET'])
def manage_checkouts():
    role_required_volunteer_librarian()
    borrowed_books = BorrowedBook.query.filter(BorrowedBook.is_verified == False,BorrowedBook.rejected_at == None).all()
    approved_books = BorrowedBook.query.filter(BorrowedBook.is_verified == True).all()
    rejected_checkouts = BorrowedBook.query.filter(BorrowedBook.rejected_at != None).all()
    csrf_form = CSRFProtectForm()

    if request.method == 'POST':
        if csrf_form.validate_on_submit():
            borrowed_book_id = request.form.get('borrowed_book_id')
            action = request.form.get('action')

            try:
                # Find the specific BorrowedBook instance by its ID
                borrowed_book = BorrowedBook.query.get(borrowed_book_id)

                if borrowed_book:
                    if action == 'approve':
                        # Update borrowed book status to approved
                        borrowed_book.is_verified = True
                        db.session.commit()
                        flash(f'Approved checkout for {borrowed_book.student.name}', 'success')
                        print(f'Approved checkout for {borrowed_book.student.name}', 'success')
                    elif action == 'reject':
                        # Update borrowed book status to rejected
                        borrowed_book.rejected_at = datetime.utcnow()
                        db.session.commit()
                        flash(f'Rejected checkout for {borrowed_book.student.name}', 'success')
                        print(f'Rejected checkout for {borrowed_book.student.name}', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error performing action: {str(e)}', 'error')
                print(f'Error performing action: {str(e)}', 'error')

        return redirect(url_for('lib.manage_checkouts'))

    return render_template('VerifyCheckout.html', borrowed_books=borrowed_books, approved_books=approved_books, rejected_checkouts=rejected_checkouts, form=csrf_form)

@lib.route('/direct_checkout', methods=['GET', 'POST'])
@login_required
def direct_checkout():
    role_required_volunteer_librarian()
    
    unique_languages = db.session.query(Book.language).distinct().all()
    unique_languages = [lang[0] for lang in unique_languages]
    verified_students = User.query.filter(User.is_verified == True, User.role.in_(['Student', 'Volunteer'])).all()
    try:
        csrf_form = CSRFProtectForm()
        book_search = request.args.get('book_search', '')
        book_language = request.args.get('book_language', '')
        student_search = request.args.get('student_search', '')
        student_department = request.args.get('student_department', '')
        page = request.args.get('page', 1, type=int)

        if request.method == 'POST' and 'selected_book_id' in request.form:
            selected_book_id = request.form.get('selected_book_id')
            selected_students = request.form.getlist('selected_students')

            for student_id in selected_students:
                due_date = datetime.utcnow() + timedelta(days=14)
                borrowed_book = BorrowedBook(
                    student_id=student_id,
                    book_id=selected_book_id,
                    borrowed_date=datetime.utcnow(),
                    due_date=due_date,
                    is_verified=True
                )
                db.session.add(borrowed_book)
            db.session.commit()
            flash('Books checked out successfully!', 'success')
            print('Books checked out successfully!')
            return redirect(url_for('lib.direct_checkout'))

        book_query = Book.query
        if book_search:
            book_query = book_query.filter(or_(Book.title.ilike(f'%{book_search}%'), Book.author.ilike(f'%{book_search}%')))
        if book_language:
            book_query = book_query.filter_by(language=book_language)
        
        books = book_query.paginate(page=page, per_page=10)

        student_query = User.query.filter_by(role='Student')
        if student_search:
            student_query = student_query.filter(or_(User.name.ilike(f'%{student_search}%'), User.roll_number.ilike(f'%{student_search}%')))
        if student_department:
            student_query = student_query.filter_by(department=student_department)
        
        students = student_query.paginate(page=page, per_page=10)

        book_languages = db.session.query(Book.language.distinct()).all()
        book_languages = [lang[0] for lang in book_languages]
        student_departments = db.session.query(User.department.distinct()).all()
        student_departments = [dept[0] for dept in student_departments]

        return render_template('DirectCheckout.html', form=csrf_form, books=books,verified_students=verified_students, students=students,unique_languages=unique_languages, book_languages=book_languages, student_departments=student_departments, book_search=book_search, book_language=book_language, student_search=student_search, student_department=student_department)

    except Exception as e:
        print(f"Error in direct_checkout: {str(e)}")
        flash('An error occurred. Please try again later.', 'danger')
        return redirect(url_for('lib.index'))  # Redirect to appropriate error page or handle as needed

# ────────────────────────────────────────────────────────────────
# Route: GET + POST → Volunteer Password Reset Page
# Shows list of users (students + co-volunteers) and handles reset
# ────────────────────────────────────────────────────────────────
@lib.route("/reset-password", methods=["GET", "POST"])
@login_required
def password_reset_page():
    role_required_volunteer_librarian()
    try:
        # ✅ Restrict access to volunteers only
        if current_user.role.lower() != "volunteer":
            flash("Unauthorized access.", "danger")
            logger.warning(f"[SECURITY] Unauthorized access attempt by {current_user.email}")
            return redirect(url_for("views.home"))

        # ───── Handle password reset POST ─────
        if request.method == "POST":
            form_type = request.form.get("form_type", "").strip()
            target_id = request.form.get("student_id")  # Works for both student or volunteer
            new_password = request.form.get("new_password", "").strip()

            logger.debug(f"[DEBUG] Password reset submitted: target_id={target_id}, pwd_len={len(new_password) if new_password else 'empty'}")

            if form_type != "volunteer_password_reset":
                flash("Invalid form submission.", "danger")
                logger.warning("[WARNING] Invalid form_type submitted.")
                return redirect(url_for("lib.password_reset_page"))

            if not target_id:
                flash("Missing user ID.", "warning")
                return redirect(url_for("lib.password_reset_page"))

            # ✅ Fetch target user (must be Student or Volunteer, not others)
            target_user = User.query.filter(User.id == target_id, User.role.in_(["Student", "Volunteer"])).first()

            if not target_user:
                flash("User not found or invalid role.", "danger")
                logger.warning(f"[ERROR] No valid user for reset found for ID: {target_id}")
                return redirect(url_for("lib.password_reset_page"))

            # ✅ Default password fallback
            if not new_password:
                new_password = "Student@123"
                logger.info(f"[INFO] Default password used for {target_user.email} by {current_user.email}")

            # ✅ Validate password strength
            if len(new_password) < 8:
                flash("Password must be at least 8 characters.", "warning")
                logger.warning(f"[WARNING] Weak password attempted by {current_user.email} for {target_user.email}")
                return redirect(url_for("lib.password_reset_page"))

            # ✅ Hash and update password
            target_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()

            flash(f"Password reset successfully for {target_user.name}.", "success")
            logger.info(f"[SUCCESS] {current_user.email} reset password for {target_user.role.lower()} {target_user.email}")
            return redirect(url_for("lib.password_reset_page"))

    except Exception as e:
        logger.exception("[ERROR] Password reset process failed.")
        flash("Something went wrong. Please try again later.", "danger")

    # ───── Handle GET Request: Load eligible users ─────
    students = User.query.filter_by(role="Student").all()
    co_volunteers = User.query.filter_by(role="Volunteer").filter(User.id != current_user.id).all()

    return render_template("ResetStudentPassword.html", students=students, co_volunteers=co_volunteers)



# ────────────────────────────────────────────────────────────────
# Route: POST → Volunteer Resets Student Password
# Handles both default and custom password updates
# ────────────────────────────────────────────────────────────────
@lib.route('/reset-password', methods=['POST'])
@login_required
def reset_student_password():
    role_required_volunteer_librarian()

    try:
        student_id = request.form.get('student_id')
        new_password = request.form.get('new_password', '').strip()

        # Validate student existence
        student = User.query.get(student_id)
        if not student or student.role != "Student":
            flash("Student not found.", "danger")
            logger.warning(f"[DEBUG] No valid student found for ID: {student_id}")
            return redirect(url_for('lib.password_reset_page'))

        # Use default password if custom one is blank
        if not new_password:
            new_password = "Student@123"
            logger.info(f"[INFO] Default password set for {student.email} by {current_user.email}")

        # Enforce minimum length
        if len(new_password) < 8:
            flash("Password must be at least 8 characters.", "warning")
            logger.warning(f"[WARNING] Weak password attempted by {current_user.email}")
            return redirect(url_for('lib.password_reset_page'))

        # Hash and update password
        hashed_pwd = generate_password_hash(new_password, method='pbkdf2:sha256')
        student.password = hashed_pwd
        db.session.commit()

        flash(f"Password for {student.name} has been updated.", "success")
        logger.info(f"[SUCCESS] {current_user.email} reset password for student {student.email}")
        return redirect(url_for('lib.password_reset_page'))

    except Exception as e:
        logger.exception("[ERROR] Student password reset failed.")
        flash("Something went wrong. Please try again later.", "danger")
        return redirect(url_for('lib.password_reset_page'))

