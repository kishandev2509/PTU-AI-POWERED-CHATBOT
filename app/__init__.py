from flask import Flask
import os
from app.app_utils import register_utils
from app.extensions import login_manager
from app.ptu_utils import fetch_ptu_notices
from utils.logger import setup_logger
from app.extensions import db
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash
from utils.scheduler import start_scheduler
from app.routes import routes
from app.auth import auth_bp
from app.chatbot.routes import chatbot_bp

def reset_db(app,db):
    from database.models import User
    db.drop_all()
    db.create_all()
    app.logger.info("Database tables recreated successfully")
    # Create a test user
    test_user = User(
        username="testuser",
        email="test@example.com",
        password=generate_password_hash("test123"),
        full_name="Test User",
        course="B.Tech",
        semester="4th",
        enrollment_number="12345",
    )
    db.session.add(test_user)

    try:
        db.session.commit()
        app.logger.info("Admin user and test user created successfully")
    except Exception as e:
        db.session.rollback()
        app.logger.exception(f"Error creating users: {e}")


def create_app(basedir):
    app = Flask(__name__)
    
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "NO_SECRECT_KEY_FOUND_IN_ENVIRONMENT")
    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{os.path.join(basedir,"database", "student_portal.db")}'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
    csrf = CSRFProtect(app)  # noqa: F841
    
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    app.register_blueprint(routes)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)

    # --- Logging ---
    log_dir = os.path.join(basedir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    app.logger = setup_logger("app")
    app.logger.info("Flask app created and logging configured.")

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    with app.app_context():
        db.create_all()
        # reset_db(app,db)
        register_utils(app)
        fetch_ptu_notices()
        start_scheduler()
        
    return app

if __name__ == "__main__":
    app = create_app(os.path.abspath(os.path.dirname(__file__)))
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
