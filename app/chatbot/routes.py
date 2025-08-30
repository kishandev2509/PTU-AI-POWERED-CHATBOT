from datetime import datetime
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from app.chatbot.forms import SupportForm
from app.chatbot.utils import get_response, send_email_to_support
from dotenv import load_dotenv
from app.chatbot.webpage_data import quick_link_categories
from database.models import ChatMessage
from utils.logger import setup_logger
from app.extensions import db

load_dotenv()
chatbot_bp = Blueprint("chatbot", __name__)
logger = setup_logger("chatbot.routes")

@chatbot_bp.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        try:
            user_timestamp = datetime.now()
            user_id = current_user.id
            user_message = request.json.get("message", "").strip()
            if not user_message:
                return jsonify({"response": "Please enter a message."})
            
            # Get bot response
            response = get_response(user_message)
            chat_message = ChatMessage(user_id=user_id,bot_response=response,user_message = user_message, user_timestamp=user_timestamp)
            print(chat_message)
            try:
                db.session.add(chat_message)
                db.session.commit()
                logger.info("History Saved")
            except Exception as e:
                logger.exception(f"Could not save history: {e}")

            return jsonify({"success": True, "response": response})

        except Exception as e:
            logger.exception(f"Error in chat endpoint: {str(e)}")
            return jsonify({"success": False, "response": "An error occurred. Please try again."})
    return render_template("chat.html", form=SupportForm(), categories=quick_link_categories)


@chatbot_bp.route("/get_chat_history")
@login_required
def get_chat_history():
    try:
        chat_history = current_user.chat_messages
        chat_list = [chat_message.to_dict() for chat_message in chat_history]
        return jsonify({"history": chat_list})
    except Exception as e:
        logger.exception(f"Error fetching chat history: {str(e)}")
        return jsonify({"history": [], "error": str(e)})


@chatbot_bp.route("/clear_chat_history")
def clear_chat_history():
    try:
        if current_user.id:
            ChatMessage.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        logger.exception(f"Error clearing chat history: {str(e)}")
        return jsonify({"success": False})


@chatbot_bp.route("/download/<doc_type>/<course>")
def download_document(doc_type, course):
    try:
        # pdf_path = ptu_utils.get_pdf_path(doc_type, course)
        # if pdf_path and os.path.exists(pdf_path):
        #     return send_file(pdf_path, as_attachment=True)
        return "File not found", 404
    except Exception as e:
        logger.exception(f"Error downloading file: {str(e)}")
        return "Error downloading file", 500


@chatbot_bp.route("/send_support_email", methods=["POST"])
def send_support_email():
    form = SupportForm()
    name = form.name.data
    email = form.email.data
    query = form.query.data

    if not all([name, email, query]):
        return jsonify({"success": False, "message": "Missing required fields"})

    body = f"Name: {name}\nEmail: {email}\nQuery: {query}"

    subject = f"Support Request from {name}"
    msg = send_email_to_support(subject, body)
    return jsonify(msg)
