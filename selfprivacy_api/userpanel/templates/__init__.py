import os
from datetime import datetime
from fastapi.templating import Jinja2Templates
from pytz import timezone


def format_datetime(
    value: datetime | None, format="%Y-%m-%d %H:%M:%S", tz_str: str = None
):
    if value is None:
        return ""
    if tz_str:
        tz = timezone(tz_str)
        value = value.astimezone(tz)
        return f"{value.strftime(format)} ({tz.zone})"

    return value.strftime(format)


templates = Jinja2Templates(directory=os.path.dirname(__file__))
templates.env.filters["format_datetime"] = format_datetime
