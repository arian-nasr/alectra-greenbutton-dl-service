from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_dates_last_2_weeks() -> tuple[datetime, datetime]:
    now = datetime.now(tz=ZoneInfo('America/Toronto'))
    two_weeks_ago = now - timedelta(weeks=2)
    return two_weeks_ago, now