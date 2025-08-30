from datetime import datetime
from bs4 import BeautifulSoup
import requests
from app.extensions import db
from database.models import Notice
from utils.logger import setup_logger


logger = setup_logger("app.ptu_utils")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def fetch_ptu_notices():
    try:
        # --- OPTIMIZATION: Step 1 ---
        # Fetch all existing notice titles from the DB in ONE query.
        # A set provides extremely fast lookups.
        existing_titles = {n.title for n in Notice.query.with_entities(Notice.title).all()}
        logger.info(f"Found {len(existing_titles)} existing notice titles in the database.")

        url = "https://ptu.ac.in/noticeboard-main/"
        response = requests.get(url, timeout=15) # Add a timeout
        soup = BeautifulSoup(response.text, "html.parser")

        notice_table = soup.find("table")
        if not notice_table:
            logger.warning("No notice table found on the webpage.")
            return []

        notices_to_add = []
        rows = notice_table.find_all("tr")[1:]

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            title = cols[0].text.strip()
            date_str = cols[1].text.strip()
            link = cols[2].find("a")["href"] if cols[2].find("a") else None

            # --- OPTIMIZATION: Step 2 ---
            # Check against the Python set instead of querying the database. This is instant.
            if title and date_str and title not in existing_titles:
                try:
                    date_posted = datetime.strptime(date_str, "%d/%m/%Y").date()
                    notice = Notice(title=title, date_posted=date_posted, link=link)
                    notices_to_add.append(notice)
                    # Add to the set as well to handle duplicates from the same scrape
                    existing_titles.add(title)
                except ValueError as e:
                    logger.error(f"Error parsing date '{date_str}' for title '{title}': {e}")
                    continue

        if notices_to_add:
            try:
                db.session.bulk_save_objects(notices_to_add)
                db.session.commit()
                logger.info(f"Successfully added {len(notices_to_add)} new notices to the database.")
            except Exception as e:
                logger.exception(f"Database error while saving new notices: {e}")
                db.session.rollback()

        return notices_to_add

    except requests.RequestException as e:
        logger.exception(f"Error fetching PTU notices webpage: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred in fetch_ptu_notices: {e}")

    return []