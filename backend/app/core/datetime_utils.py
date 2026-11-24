import datetime

def utc_now() -> datetime.datetime:
    """Return current UTC datetime without tzinfo for consistent DB comparisons and zero deprecations."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
