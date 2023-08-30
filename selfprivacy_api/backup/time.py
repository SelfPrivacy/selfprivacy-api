from datetime import datetime, timedelta, time


def same_day(a: datetime, b: datetime) -> bool:
    return a.date() == b.date()


def same_week(a: datetime, b: datetime) -> bool:
    # doing the hard way because weeks traverse the edges of years
    zerobased_weekday = a.isoweekday() - 1
    start_of_day = datetime.combine(a.date(), time.min)
    start_of_week = start_of_day - timedelta(days=zerobased_weekday)
    end_of_week = start_of_week + timedelta(days=7)

    if b >= start_of_week and b <= end_of_week:
        return True
    return False


def same_month(a: datetime, b: datetime) -> bool:
    return a.month == b.month and a.year == b.year


def same_year(a: datetime, b: datetime) -> bool:
    return a.year == b.year


def same_lifetime_of_the_universe(a: datetime, b: datetime) -> bool:
    return True
