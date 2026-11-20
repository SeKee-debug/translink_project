import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class DailyBudget:
    """Keeps track of how many API requests we've made today (in `tz`) and says no once we hit the cap.

    The count is only kept in memory, so if the script restarts it goes back to 0. I'm okay with
    that because the collection window by itself already keeps a day under the cap. This is more
    of a backup in case of a bug, like the loop forgetting to sleep.
    """

    def __init__(self, cap: int, tz: ZoneInfo) -> None:
        self.cap = cap
        self.tz = tz
        self.requests_today = 0
        self.counter_date: date = datetime.now(tz).date()
        self._warned_today = False

    def try_consume(self) -> bool:
        """Returns True if we can make one more request (it gets counted right away), False if we're at today's cap."""
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

        # Count it before the fetch, since a request that fails still hits TransLink's server
        self.requests_today += 1
        return True
