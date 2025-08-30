from datetime import datetime, timezone


# -------- Filters --------
def filter_elapsed(date):
    if not date:
        return "N/A"
    try:
        diff = datetime.now(timezone.utc) - date
    except TypeError:
        diff = datetime.utcnow() - date
    if diff.days > 0:
        return f"{diff.days} day(s) ago"
    elif diff.seconds >= 3600:
        return f"{diff.seconds // 3600} hour(s) ago"
    elif diff.seconds >= 60:
        return f"{diff.seconds // 60} minute(s) ago"
    else:
        return f"{diff.seconds} second(s) ago"


def filter_uppercase(text):
    return text.upper()


# -------- Context Processors --------
def context_current_year():
    return {"current_year": datetime.now().year}


# -------- Auto Registration --------
def register_utils(app):
    """
    Auto-registers all functions starting with 'filter_' as Jinja filters,
    and all functions starting with 'context_' as context processors.
    """
    for name, func in globals().items():
        if callable(func):
            if name.startswith("filter_"):
                # register filter without prefix
                app.jinja_env.filters[name.replace("filter_", "")] = func
            elif name.startswith("context_"):
                app.context_processor(func)
