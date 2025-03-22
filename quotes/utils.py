from datetime import time, timedelta, datetime
from quotes.models import Quote

def get_available_hours_for_date(date, hours_requested=2):
    start_hour = 9
    end_hour = 17
    interval = 30  # minutes
    duration_minutes = max(hours_requested * 60, 120)  # Minimum 2 hours

    # Generate all potential 30-min slots
    all_slots = []
    current = datetime.combine(date, time(hour=start_hour))
    end = datetime.combine(date, time(hour=end_hour))
    while current + timedelta(minutes=duration_minutes) <= end:
        all_slots.append(current.time())
        current += timedelta(minutes=interval)

    # Collect unavailable time ranges
    unavailable_ranges = []
    for quote in Quote.objects.filter(date=date):
        duration = max(quote.hours_requested or 2, 2)
        start = datetime.combine(date, quote.hour)
        end = start + timedelta(hours=duration)
        unavailable_ranges.append((start.time(), end.time()))

    # Check if each slot fits entirely in available range
    valid_slots = []
    for slot in all_slots:
        start = datetime.combine(date, slot)
        end = start + timedelta(minutes=duration_minutes)

        overlaps = any(
            (start.time() < u_end and end.time() > u_start)
            for u_start, u_end in unavailable_ranges
        )
        if not overlaps:
            valid_slots.append(slot)

    return valid_slots
