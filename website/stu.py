from flask import Blueprint,render_template,request,session, url_for, redirect,flash, current_app, jsonify, json
from flask_login import login_required,current_user
from .models import Book,BorrowedBook,User
from datetime import datetime,timedelta,timezone
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from sqlalchemy import or_, func, desc, asc
import os
import logging
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

logger = logging.getLogger(__name__)

stu = Blueprint('stu', __name__)

@stu.route('/checkoutbooks', methods=['GET', 'POST'])
@login_required
def CheckoutBooks():
    search_query = request.args.get('search', '')
    lang_filter  = request.args.get('language', '')
    sort_option  = request.args.get('sort', 'newest')
    page         = request.args.get('page', 1, type=int)

    # --- POST: checkout ---
    if request.method == 'POST':
        raw = request.form.get('selected_books', '[]')
        try:
            ids = list(map(int, json.loads(raw)))
        except Exception as e:
            print("🔴 [DEBUG] Failed to parse selected_books:", raw, "Error:", e)
            flash('Invalid selection payload.', 'danger')
            return redirect(url_for('stu.CheckoutBooks'))

        print("🟢 [DEBUG] Selected IDs to checkout:", ids)
        if not ids:
            flash('Select at least one book.', 'warning')
            return redirect(url_for('stu.CheckoutBooks'))

        try:
            for bid in ids:
                book = Book.query.get(bid)
                print(f"   → [DEBUG] Processing book id={bid}, qty={getattr(book,'quantity',None)}")
                if book and book.quantity > 0:
                    book.quantity -= 1
                    due = datetime.now(timezone.utc) + timedelta(days=14)
                    bb = BorrowedBook(
                        student_id=current_user.id,
                        book_id=bid,
                        borrowed_date=datetime.now(timezone.utc),
                        due_date=due,
                        is_verified=False
                    )
                    db.session.add(bb)
                else:
                    print(f"   ⚠️ [DEBUG] Cannot checkout book id={bid}: not found or zero quantity")
            db.session.commit()
            flash('Checked out! Await verification.', 'success')
            print("🟢 [DEBUG] Commit successful.")
        except Exception as e:
            db.session.rollback()
            print("🔴 [DEBUG] Checkout error:", e)
            flash(f'Error during checkout: {e}', 'danger')
        return redirect(url_for('stu.CheckoutBooks'))

    # --- GET: build query ---
    q = Book.query
    if search_query:
        term = f"%{search_query}%"
        q = q.filter(or_(Book.title.ilike(term),
                         Book.author.ilike(term),
                         Book.isbn.ilike(term)))
    if lang_filter:
        q = q.filter(Book.language == lang_filter)

    # Sorting
    if sort_option == 'newest':
        q = q.order_by(desc(Book.date_of_donation))
    elif sort_option == 'oldest':
        q = q.order_by(Book.date_of_donation)
    elif sort_option == 'a_z':
        q = q.order_by(Book.title.asc())
    elif sort_option == 'z_a':
        q = q.order_by(Book.title.desc())
    elif sort_option == 'popular':
        q = q.outerjoin(BorrowedBook).group_by(Book.id).order_by(func.count(BorrowedBook.id).desc())
    else:
        q = q.order_by(desc(Book.added_at))

    books = q.paginate(page=page, per_page=8, error_out=False)

    # Attach donor_data
    for book in books.items:
        if book.donor:
            donated = [
                {"title": b.title, "date": b.date_of_donation.strftime("%d %b %Y")}
                for b in book.donor.books
            ]
            book.donor_data = {
                "name": book.donor.name,
                "dept": book.donor.department,
                "yog": book.donor.year_of_graduation,
                "donated": donated
            }
        else:
            book.donor_data = {"name": "N/A", "dept": "", "yog": "", "donated": []}

    unique_languages = [l[0] for l in db.session.query(Book.language.distinct()).all()]
    sort_options = [
        ('newest',  'New Arrivals'),
        ('popular', 'Popular'),
        ('oldest',  'Oldest'),
        ('a_z',     'A → Z'),
        ('z_a',     'Z → A'),
    ]

    return render_template(
        'CheckoutBooks.html',
        books=books,
        search_query=search_query,
        lang_filter=lang_filter,
        sort_option=sort_option,
        unique_languages=unique_languages,
        sort_options=sort_options
    )

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