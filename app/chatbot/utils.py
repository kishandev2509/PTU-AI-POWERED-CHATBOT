from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib

from flask_login import current_user
from app.chatbot.groq_model import answer
from app.chatbot.tfid import TFIDModel
from utils.logger import setup_logger

logger = setup_logger("chatbot.utils")
tf_id_model = TFIDModel()

# def get_response(user_message: str) -> str:
#     """
#     returns the response from the llm for the given quesry about ptu
#     """
#     try:
#         tf_id_model = TFIDModel()
#         return tf_id_model.get_intent_response(user_message)
#     except NoIntentFound:
#         return answer(user_message)


def get_response(user_message: str) -> str:
    """
    returns the response from the llm for the given query about ptu
    """
    intent = tf_id_model.get_response(user_message)
    return answer(user_message, intent)


def send_email_to_support(email_subject: str, email_body: str, bcc: str = None):
    import traceback

    # Email configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SUPPORT_EMAILS = os.getenv("SUPPORT_EMAILS", "support@ptu.ac.in")
    print(SUPPORT_EMAILS)

    new_body = f"{email_body}\n\nThis is an automated message from the PTU Chatbot support system.\nThis request is sent by user:\nName = {current_user.full_name}\nEmail = {current_user.email}\nCourse = {current_user.course}\nSemester = {current_user.semester}\nRollNo = {current_user.enrollment_number}"

    all_recipients = [email.strip() for email in SUPPORT_EMAILS.split(',')]
    # Add the BCC recipient to the list if one was provided
    if bcc:
        all_recipients.append(bcc)

    # Create email message
    response_msg = MIMEMultipart()
    response_msg["From"] = EMAIL_USERNAME
    response_msg["To"] = SUPPORT_EMAILS
    response_msg["Subject"] = email_subject
    response_msg.attach(MIMEText(new_body, "plain"))

    try:
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(response_msg, to_addrs=all_recipients)
            log_message = f"Support email sent successfully to {SUPPORT_EMAILS}"
            if bcc:
                log_message += f" with BCC to {bcc}"
            logger.info(log_message)
        response_msg = {
            "success": True,
            "message": "Email sent successfully",
        }
    except smtplib.SMTPAuthenticationError:
        logger.exception("SMTP Authentication Error: Please check your email credentials")
        logger.exception(traceback.format_exc())
        response_msg = {
            "success": False,
            "message": "Email authentication failed. Please check server configuration.",
        }
    except smtplib.SMTPException as e:
        logger.exception(f"SMTP Error: {str(e)}")
        logger.exception(traceback.format_exc())
        response_msg = {
            "success": False,
            "message": "Failed to send email. Please try again later.",
        }
    except Exception as e:
        logger.exception(f"General error sending email: {str(e)}")
        logger.exception(traceback.format_exc())
        response_msg = {
            "success": False,
            "message": "Failed to send email. Please try again later.",
        }
    return response_msg
