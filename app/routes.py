from datetime import datetime, timezone
import os
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for, send_from_directory
from flask_login import current_user, login_required
from app.ptu_utils import allowed_file, fetch_ptu_notices
from database.models import ActivityLog, Notice, SupportTicket
from werkzeug.security import generate_password_hash
from app.extensions import db
from werkzeug.utils import secure_filename
from app.forms import ProfileForm, SupportTicketForm
from utils.logger import setup_logger

routes = Blueprint("routes", __name__)
logger = setup_logger("app.routes")


# Routes
@routes.route("/")
def index():
    return render_template("home.html")


@routes.route("/dashboard")
@login_required
def dashboard():
    # Fetch latest notices
    notices = Notice.query.order_by(Notice.date_posted.desc()).limit(10).all()
    return render_template("dashboard.html", notices=notices)


@routes.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Update user profile
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.course = form.course.data
        current_user.semester = form.semester.data
        current_user.enrollment_number = form.enrollment_number.data
        if form.new_password.data:
            current_user.password = generate_password_hash(form.new_password.data)

        activity_log = ActivityLog(user_id=current_user.id, action="Profile Updated", icon="bi bi-person-check", description="You updated your profile information")

        try:
            db.session.add(activity_log)
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error Updating Profile: {e}")
            flash("Error updating profile. Please try again.", "error")

        return redirect(url_for("routes.profile"))

    return render_template("profile.html", form=form)


@routes.route("/support_tickets", methods=["GET", "POST"])
@login_required
def support_tickets():
    form = SupportTicketForm()
    if form.validate_on_submit():
        subject = form.subject.data
        message = form.message.data

        if not subject or not message:
            flash("Please fill in all fields", "error")
            return redirect(url_for("routes.support_tickets"))

        ticket = SupportTicket(user_id=current_user.id, subject=subject, message=message)
        activity_log = ActivityLog(user_id=current_user.id, action="Ticket Created", icon="bi bi-ticket", description="You created a new support ticket")

        try:
            db.session.add(ticket)
            db.session.add(activity_log)
            db.session.commit()
            flash("Query created successfully!", "success")
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error Creating Query: {e}")
            flash("Error creating query. Please try again.", "error")

        return redirect(url_for("routes.support_tickets"))

    # Get queries based on view type
    view = request.args.get("view", "inbox")

    if view == "trash":
        tickets = SupportTicket.query.filter_by(user_id=current_user.id, deleted=True).order_by(SupportTicket.deleted_at.desc()).all()
    elif view == "archive":
        tickets = SupportTicket.query.filter_by(user_id=current_user.id, archived=True, deleted=False).order_by(SupportTicket.archived_at.desc()).all()
    elif view == "starred":
        tickets = SupportTicket.query.filter_by(user_id=current_user.id, starred=True, deleted=False, archived=False).order_by(SupportTicket.created_at.desc()).all()
    else:  # inbox
        tickets = SupportTicket.query.filter_by(user_id=current_user.id, deleted=False, archived=False).order_by(SupportTicket.created_at.desc()).all()

    views_list = ['inbox', 'sent', 'starred', 'archive', 'trash']
    views_list_icons = ['inbox-fill', 'send-fill', 'star-fill', 'archive-fill', 'trash-fill']

    return render_template("support_tickets.html", tickets=tickets, view=view, form=form, zipped_views=zip(views_list,views_list_icons))


@routes.route("/upload_profile_photo", methods=["POST"])
@login_required
def upload_profile_photo():
    if "photo" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "profile_photos")
        # Create a unique filename
        filename = secure_filename(f"{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")

        # Delete old profile photo if it exists
        if current_user.profile_photo:
            old_photo_path = os.path.join(upload_folder, current_user.profile_photo)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)

        # Save the new photo
        file.save(os.path.join(upload_folder, filename))

        # Update database
        current_user.profile_photo = filename
        activity_log = ActivityLog(user_id=current_user.id, action="Profile Photo Updated", icon="bi bi-person-check", description="You updated your profile Photo")
        db.session.add(activity_log)
        db.session.commit()

        return jsonify({"success": True, "photo_url": f"/profile_photo/{filename}"})

    return jsonify({"success": False, "error": "Invalid file type"}), 400


@routes.route("/profile_photo/<filename>")
def get_profile_photo(filename):
    upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "profile_photos")
    return send_from_directory(upload_folder, filename)


@routes.route("/delete_query", methods=["POST"])
@login_required
def delete_query():
    data = request.get_json()
    query_id = data.get("query_id")
    permanent = data.get("permanent", False)

    ticket = SupportTicket.query.get(query_id)
    if ticket and ticket.user_id == current_user.id:
        if permanent:
            db.session.delete(ticket)
            activity_log = ActivityLog(user_id=current_user.id, action="Ticket Deleted", icon="bi bi-ticket", description="You deleted a support ticket permanentaly")
            db.session.add(activity_log)
        else:
            ticket.deleted = True
            ticket.deleted_at = datetime.now(timezone.utc)
            activity_log = ActivityLog(user_id=current_user.id, action="Ticket Moved To Trash", icon="bi bi-ticket", description="You moved a support ticket to trash")

        try:
            db.session.add(activity_log)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": False, "error": "Query not found"}), 404


@routes.route("/restore_query", methods=["POST"])
@login_required
def restore_query():
    data = request.get_json()
    query_id = data.get("query_id")

    ticket = SupportTicket.query.get(query_id)
    if ticket and ticket.user_id == current_user.id:
        ticket.deleted = False
        activity_log = ActivityLog(user_id=current_user.id, action="Ticket Restored", icon="bi bi-ticket", description="You restored a support ticket from trash to inbox")
        try:
            db.session.add(activity_log)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": False, "error": "Query not found"}), 404


@routes.route("/toggle_star", methods=["POST"])
@login_required
def toggle_query_star():
    data = request.get_json()
    query_id = data.get("query_id")

    ticket = SupportTicket.query.get(query_id)
    if ticket and ticket.user_id == current_user.id:
        ticket.starred = not ticket.starred
        activity_log = ActivityLog(user_id=current_user.id, action="Ticket Starred", icon="bi bi-ticket", description="You starred a support ticket")
        try:
            db.session.add(activity_log)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": False, "error": "Query not found"}), 404


@routes.route("/toggle_archive", methods=["POST"])
@login_required
def toggle_query_archive():
    data = request.get_json()
    query_id = data.get("query_id")
    print(query_id)
    ticket = SupportTicket.query.get(query_id)
    if ticket and ticket.user_id == current_user.id:
        ticket.archived = not ticket.archived

        try:
            if ticket.archived:
                activity_log = ActivityLog(user_id=current_user.id, action="Ticket Archived", icon="bi bi-ticket", description="You archived a support ticket")
            else:
                activity_log = ActivityLog(user_id=current_user.id, action="Ticket Unarchived", icon="bi bi-ticket", description="You unarchived a support ticket")
            db.session.add(activity_log)
            db.session.commit()
            return jsonify({"success": True, "archived": ticket.archived})
        except Exception as e:
            print(e)
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": False, "error": "Query not found"}), 404


@routes.route("/notices")
@login_required
def notices():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    notices = Notice.query.order_by(Notice.date_posted.desc()).paginate(page=page, per_page=per_page)
    return render_template("notices.html", notices=notices)


@routes.route("/refresh_notices")
@login_required
def refresh_notices():
    try:
        new_notices = fetch_ptu_notices()
        if new_notices:
            flash(f"Successfully added {len(new_notices)} new notices!", "success")
        else:
            flash("No new notices found.", "info")
    except Exception as e:
        flash(f"Error refreshing notices: {str(e)}", "error")

    return redirect(url_for("routes.notices"))
