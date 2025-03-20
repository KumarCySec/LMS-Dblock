from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import or_
from datetime import datetime
from .models import Book, User, Donor,BorrowedBook
from . import db
from .forms import CSRFProtectForm

MA = Blueprint('MasterAdmin', __name__)

@MA.route('/managelibrarian', methods=['GET', 'POST'])
@login_required
def manage_librarians():
    verified_librarians = User.query.filter(User.is_verified == True, User.role.in_(['Librarian'])).all()
    unverified_librarians = User.query.filter(User.is_verified == False, User.role.in_(['Librarian']), User.rejected_at == None).all()
    rejected_librarians = User.query.filter(User.rejected_at != None).all()  # Fetching rejected librarians
    csrf_form = CSRFProtectForm()

    if request.method == 'POST':
        if csrf_form.validate_on_submit():
            librarian_id = request.form.get('librarian_id')
            action = request.form.get('action')
            print(f"action is {action}")

            librarian = User.query.get(librarian_id)
            
            if librarian:
                try:
                    if action == 'verify':
                        librarian.is_verified = True
                        db.session.commit()
                        flash(f'{librarian.name} has been verified successfully!', category='success')
                    elif action == 'deverify':
                        librarian.is_verified = False
                        db.session.commit()
                        flash(f'{librarian.name} has been deverified!', category='success')
                        print(f'{librarian.name} has been deverified!success')
                    elif action == 'reject':
                        librarian.rejected_at = datetime.utcnow()
                        db.session.commit()
                        flash(f'{librarian.name} has been rejected!', category='success')
                    elif action == 'delete':
                        db.session.delete(librarian)
                        db.session.commit()
                        flash(f'{librarian.name} has been deleted successfully!', category='success')
                    elif action == 'delete_all_rejected':
                        rejected_librarians = User.query.filter(User.rejected_at != None).all()
                        for rejected_librarian in rejected_librarians:
                            db.session.delete(rejected_librarian)
                        db.session.commit()
                        flash('All rejected librarians have been deleted successfully!', category='success')
                except Exception as e:
                    flash(f'Error performing action: {str(e)}', category='error')
                    print(f'Error performing action: {str(e)}error')
                    db.session.rollback()
            else:
                flash('Student not found!', category='error')

        return redirect(url_for('MasterAdmin.manage_librarians'))

    return render_template('ManageLibrarians.html', verified_librarians=verified_librarians, unverified_librarians=unverified_librarians, rejected_librarians=rejected_librarians, form=csrf_form)