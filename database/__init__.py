
from app.extensions import login_manager
from database.models import Admin, User


@login_manager.user_loader
def load_user(user_id):
    # Try to load user first
    user = User.query.get(int(user_id))
    if user:
        return user
    # If not a user, try to load admin
    return Admin.query.get(int(user_id))
