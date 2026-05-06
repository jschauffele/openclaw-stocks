import logging

from alpaca.trading.requests import GetCalendarRequest


def get_market_session_status(client) -> dict:
    try:
        clock = client.get_clock()
        now = clock.timestamp

        today = now.date()
        calendar_request = GetCalendarRequest(start=today, end=today)
        calendar_days = client.get_calendar(filters=calendar_request)

        if not calendar_days:
            logging.warning("No calendar entry returned for today; treating as market holiday/closed")
            return {
                "is_open": False,
                "reason": "market_holiday_or_closed_day",
                "current_time": str(now),
                "session_open": None,
                "session_close": None,
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        day = calendar_days[0]

        # Ensure timezone consistency
        session_open = day.open.replace(tzinfo=now.tzinfo)
        session_close = day.close.replace(tzinfo=now.tzinfo)

        if now < session_open:
            return {
                "is_open": False,
                "reason": "before_regular_session_open",
                "current_time": str(now),
                "session_open": str(session_open),
                "session_close": str(session_close),
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        if now >= session_close:
            return {
                "is_open": False,
                "reason": "after_regular_session_close",
                "current_time": str(now),
                "session_open": str(session_open),
                "session_close": str(session_close),
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        if not clock.is_open:
            return {
                "is_open": False,
                "reason": "broker_clock_closed",
                "current_time": str(now),
                "session_open": str(session_open),
                "session_close": str(session_close),
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        return {
            "is_open": True,
            "reason": "regular_session_open",
            "current_time": str(now),
            "session_open": str(session_open),
            "session_close": str(session_close),
            "next_open": str(clock.next_open),
            "next_close": str(clock.next_close),
        }

    except Exception as e:
        logging.exception("Market session lookup failed")
        return {
            "is_open": False,
            "reason": "market_session_lookup_failed",
            "error": str(e),
            "current_time": None,
            "session_open": None,
            "session_close": None,
            "next_open": None,
            "next_close": None,
        }
