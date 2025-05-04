from flask import Flask, current_app, session
from flask_sqlalchemy import SQLAlchemy
from os import path
import os
from flask_login import LoginManager
from datetime import timedelta
from flask_migrate import Migrate

db = SQLAlchemy()
DB_NAME = "Kishorebase.db"
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.secret_key = "aehfb u%R#*Y(@)hijbfka2f1we1"
    app.permanent_session_lifetime = timedelta(minutes=5)
    app.config['SECRET_KEY'] = 'fdfdg64646$%^&^%$#@#$^%$ 5484f6s4646'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'pfp')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB limit

    db.init_app(app)
    migrate.init_app(app, db)

    from .veiws import views
    from .auth import auth
    from .lib import lib
    from .stu import stu
    from .MA import MA

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(lib, url_prefix='/lib')
    app.register_blueprint(stu, url_prefix='/stu')
    app.register_blueprint(MA, url_prefix='/MasterAdmin')

    from .models import User

    with app.app_context():
        create_database()

    logman = LoginManager()
    logman.login_view = 'auth.auth_page'
    logman.init_app(app)

    @logman.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database():
    database_path = f'website/{DB_NAME}'
    try:
        if not path.exists(database_path):
            with current_app.app_context():
                db.create_all()
                print('Created Database!')
        else:
            print('Database file already exists at:', database_path)
    except Exception as e:
        print('An error occurred while creating the database:', e)
