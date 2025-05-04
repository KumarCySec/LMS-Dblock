from website import db
from datetime import datetime,timezone
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True, nullable=False)
    role = Column(String(50), nullable=False)  
    password = Column(String(150), nullable=False)
    name = Column(String(150), nullable=False)
    roll_number = Column(Integer, unique=True, nullable=True)
    phone_number = Column(String(20), nullable=True)
    department = Column(String(150), nullable=True)
    year_of_graduation = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False)
    profile_picture_url = Column(String(255), nullable=True)

    books = relationship('Book', back_populates='student')
    borrowed_books = relationship('BorrowedBook', back_populates='student')

    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}', role='{self.role}')>"


class Book(db.Model):
    __tablename__ = 'book'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    title = Column(String(150), nullable=False)
    author = Column(String(150), nullable=False)
    isbn = Column(String(20), nullable=True)
    published_date = Column(DateTime, nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    language = Column(String(20), nullable=False)
    date_of_donation = Column(DateTime, nullable=False)
    donor_id = Column(Integer, ForeignKey('donor.id'), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = relationship('User', back_populates='books')
    borrowed_by = relationship('BorrowedBook', back_populates='book')
    donor = relationship('Donor', back_populates='books')

    def __repr__(self):
        return f"<Book(title='{self.title}', author='{self.author}', isbn='{self.isbn}')>"


class BorrowedBook(db.Model):
    __tablename__ = 'borrowed_books'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('book.id'), nullable=False)
    borrowed_date = Column(DateTime, default=datetime.now, nullable=False)
    due_date = Column(DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # New field to track verification status
    rejected_at = Column(DateTime, nullable=True)

    student = relationship('User', back_populates='borrowed_books')
    book = relationship('Book', back_populates='borrowed_by')

    def __repr__(self):
        return f"<BorrowedBook(id={self.id}, student_id={self.student_id}, book_id={self.book_id}, borrowed_date={self.borrowed_date}, due_date={self.due_date})>"


class Donor(db.Model):
    __tablename__ = 'donor'

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    department = Column(String(150), nullable=False)
    year_of_graduation = Column(Integer, nullable=False)
    mobilenumber = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True)
    address = Column(String(1000), nullable=True)

    books = relationship('Book', back_populates='donor')
    

    def __repr__(self):
        return f"<Donor(name='{self.name}', department='{self.department}', year_of_graduation={self.year_of_graduation})>"

class VolunteerAssignment(db.Model):
    __tablename__ = 'volunteer_assignment'

    id = db.Column(db.Integer, primary_key=True)

    day = db.Column(db.String(10), nullable=False)  # e.g., "Monday", "Tuesday"

    volunteer1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    volunteer2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    volunteer1 = db.relationship('User', foreign_keys=[volunteer1_id])
    volunteer2 = db.relationship('User', foreign_keys=[volunteer2_id])

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('day', name='uq_volunteer_assignment_day'),
    )

    def __repr__(self):
        return f"<VolunteerAssignment(day={self.day}, volunteer1={self.volunteer1.name}, volunteer2={self.volunteer2.name})>"

class LibraryStatus(db.Model):
    __tablename__ = 'library_status'

    id = db.Column(db.Integer, primary_key=True)
    is_open = db.Column(db.Boolean, default=True)  # True for Open, False for Closed
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LibraryStatus(id={self.id}, is_open={self.is_open}, updated_at={self.updated_at})>"