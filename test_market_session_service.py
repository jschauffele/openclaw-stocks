from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from market_session_service import get_market_session_status


UTC = timezone.utc
SESSION_OPEN = datetime(2026, 5, 6, 13, 30, tzinfo=UTC)
SESSION_CLOSE = datetime(2026, 5, 6, 20, 0, tzinfo=UTC)
NEXT_OPEN = datetime(2026, 5, 7, 13, 30, tzinfo=UTC)
NEXT_CLOSE = datetime(2026, 5, 7, 20, 0, tzinfo=UTC)


class FakeClient:
    def __init__(
        self,
        *,
        now: datetime = datetime(2026, 5, 6, 14, 0, tzinfo=UTC),
        is_open: bool = True,
        calendar_days: list | None = None,
        clock_exception: Exception | None = None,
        calendar_exception: Exception | None = None,
    ) -> None:
        self.clock = SimpleNamespace(
            timestamp=now,
            is_open=is_open,
            next_open=NEXT_OPEN,
            next_close=NEXT_CLOSE,
        )
        self.calendar_days = (
            [SimpleNamespace(open=SESSION_OPEN, close=SESSION_CLOSE)]
            if calendar_days is None
            else calendar_days
        )
        self.clock_exception = clock_exception
        self.calendar_exception = calendar_exception
        self.calendar_filters = None

    def get_clock(self):
        if self.clock_exception is not None:
            raise self.clock_exception
        return self.clock

    def get_calendar(self, filters):
        if self.calendar_exception is not None:
            raise self.calendar_exception
        self.calendar_filters = filters
        return self.calendar_days


class MarketSessionServiceTests(unittest.TestCase):
    def test_regular_session_open(self) -> None:
        client = FakeClient(now=datetime(2026, 5, 6, 14, 0, tzinfo=UTC))

        result = get_market_session_status(client)

        self.assertTrue(result["is_open"])
        self.assertEqual(result["reason"], "regular_session_open")
        self.assertEqual(result["current_time"], "2026-05-06 14:00:00+00:00")
        self.assertEqual(result["session_open"], str(SESSION_OPEN))
        self.assertEqual(result["session_close"], str(SESSION_CLOSE))
        self.assertEqual(result["next_open"], str(NEXT_OPEN))
        self.assertEqual(result["next_close"], str(NEXT_CLOSE))

    def test_before_regular_session_open(self) -> None:
        client = FakeClient(now=datetime(2026, 5, 6, 13, 0, tzinfo=UTC))

        result = get_market_session_status(client)

        self.assertFalse(result["is_open"])
        self.assertEqual(result["reason"], "before_regular_session_open")
        self.assertEqual(result["current_time"], "2026-05-06 13:00:00+00:00")
        self.assertEqual(result["session_open"], str(SESSION_OPEN))
        self.assertEqual(result["session_close"], str(SESSION_CLOSE))
        self.assertEqual(result["next_open"], str(NEXT_OPEN))
        self.assertEqual(result["next_close"], str(NEXT_CLOSE))

    def test_after_regular_session_close(self) -> None:
        client = FakeClient(now=datetime(2026, 5, 6, 20, 0, tzinfo=UTC))

        result = get_market_session_status(client)

        self.assertFalse(result["is_open"])
        self.assertEqual(result["reason"], "after_regular_session_close")
        self.assertEqual(result["current_time"], "2026-05-06 20:00:00+00:00")
        self.assertEqual(result["session_open"], str(SESSION_OPEN))
        self.assertEqual(result["session_close"], str(SESSION_CLOSE))
        self.assertEqual(result["next_open"], str(NEXT_OPEN))
        self.assertEqual(result["next_close"], str(NEXT_CLOSE))

    def test_market_holiday_or_closed_day(self) -> None:
        client = FakeClient(calendar_days=[])

        result = get_market_session_status(client)

        self.assertFalse(result["is_open"])
        self.assertEqual(result["reason"], "market_holiday_or_closed_day")
        self.assertEqual(result["current_time"], "2026-05-06 14:00:00+00:00")
        self.assertIsNone(result["session_open"])
        self.assertIsNone(result["session_close"])
        self.assertEqual(result["next_open"], str(NEXT_OPEN))
        self.assertEqual(result["next_close"], str(NEXT_CLOSE))

    def test_broker_clock_closed(self) -> None:
        client = FakeClient(
            now=datetime(2026, 5, 6, 14, 0, tzinfo=UTC),
            is_open=False,
        )

        result = get_market_session_status(client)

        self.assertFalse(result["is_open"])
        self.assertEqual(result["reason"], "broker_clock_closed")
        self.assertEqual(result["current_time"], "2026-05-06 14:00:00+00:00")
        self.assertEqual(result["session_open"], str(SESSION_OPEN))
        self.assertEqual(result["session_close"], str(SESSION_CLOSE))
        self.assertEqual(result["next_open"], str(NEXT_OPEN))
        self.assertEqual(result["next_close"], str(NEXT_CLOSE))

    def test_market_session_lookup_failed(self) -> None:
        client = FakeClient(clock_exception=RuntimeError("clock unavailable"))

        result = get_market_session_status(client)

        self.assertFalse(result["is_open"])
        self.assertEqual(result["reason"], "market_session_lookup_failed")
        self.assertEqual(result["error"], "clock unavailable")
        self.assertIsNone(result["current_time"])
        self.assertIsNone(result["session_open"])
        self.assertIsNone(result["session_close"])
        self.assertIsNone(result["next_open"])
        self.assertIsNone(result["next_close"])


if __name__ == "__main__":
    unittest.main()
