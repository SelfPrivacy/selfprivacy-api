import os
from datetime import datetime
from fastapi.templating import Jinja2Templates


def format_datetime(value: datetime | None, format="%Y-%m-%d %H:%M:%S"):
    if value is None:
        return ""
    return value.strftime(format)


templates = Jinja2Templates(directory=os.path.dirname(__file__))
templates.env.filters["format_datetime"] = format_datetime
