import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class DailyBudget:
    """Counts API requests per calendar day (in `tz`) and refuses once the cap is reached.

    The count lives in memory, so restarting the process resets it to 0. That's acceptable
    because the collection window alone keeps a day under the cap; this is a safety net
    against bugs such as a loop that stops sleeping.
    """

    def __init__(self, cap: int, tz: ZoneInfo) -> None:
        self.cap = cap
        self.tz = tz
        self.requests_today = 0
        self.counter_date: date = datetime.now(tz).date()
        self._warned_today = False

    def try_consume(self) -> bool:
        """True = you may make one request (it is counted now). False = cap reached today."""
        today = datetime.now(self.tz).date()
        if today != self.counter_date:
            self.counter_date = today
            self.requests_today = 0
            self._warned_today = False

        if self.requests_today >= self.cap:
            if not self._warned_today:
                logger.warning(
                    "Daily request cap of %d reached for %s; no more fetches until midnight",
                    self.cap,
                    today.isoformat(),
                )
                self._warned_today = True
            return False

        # Count before fetching: a request that fails still reached TransLink
        self.requests_today += 1
        return True
