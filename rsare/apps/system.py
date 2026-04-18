# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.farm_app import App


@dataclass
class WaitForNotificationTimeout:
    time_created: float
    timeout: int = 0
    timeout_timestamp: float = field(init=False)

    def __str__(self):
        return f"Wait for even timeout after {self.timeout} seconds"

    def __post_init__(self):
        self.timeout_timestamp = self.time_created + self.timeout


class SystemApp(App):
    def __init__(
        self,
        name: str | None = None,
    ):
        super().__init__(name)
        self.wait_for_notification_timeout = None
        self.wait_for_next_notification: Callable = lambda: None  # type: ignore # Will be set by Environment during registration


    def wait(self, time: int = 0) -> None:
        """
        Wait a given amount of time, only to be used when you have absolutely nothing to do.
        :param time: Amount of time to wait in seconds
        """
        assert time >= 0, "Time must be non-negative"
        self.time_manager.add_offset(time)

    @agent_tool()
    def get_current_time(self) -> dict:
        """
        Get the current time, date and weekday, returned in a dict, timestamp as float (epoch), datetime as string (YYYY-MM-DD HH:MM:SS), weekday as string (Monday, Tuesday, etc.).
        :returns: a dictionary with the keys "current_timestamp" (current time as timestamp), "current_datetime" (current time as datetime), "current_weekday" (current weekday)
        """
        timestamp = self.time_manager.time()
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return {
            "current_timestamp": timestamp,
            "current_datetime": date.strftime("%Y-%m-%d %H:%M:%S"),
            "current_weekday": date.strftime("%A"),
        }

    def get_wait_for_notification_timeout(self) -> WaitForNotificationTimeout | None:
        """
        Return the current wait for event timeout, if any.
        """
        if (
            self.wait_for_notification_timeout
            and self.time_manager.time()
            >= self.wait_for_notification_timeout.timeout_timestamp
        ):
            return self.wait_for_notification_timeout
        return None

    def reset_wait_for_notification_timeout(self):
        self.wait_for_notification_timeout = None

    @agent_tool()
    def wait_for_notification(
        self,
        timeout: int = 0,
    ) -> None:
        """
        Wait for a specified amount of time or until the next notification or user message is received, whichever comes first.
        This method should only be used when there are no other tasks to perform.
        :param timeout: The maximum amount of time to wait in seconds. If a notification is received before this time elapses, the wait will end early.
        """
        # This method efficiently jumps from event to event without advancing time incrementally, making it more efficient than wait_for_notification.
        timeout = int(timeout)
        assert timeout >= 0, "Timeout must be non-negative"
        # Create a new timeout object that will be used by the notification system.
        # It will create a notification after the timeout is reached if no other notification is received in between.
        self.wait_for_notification_timeout = WaitForNotificationTimeout(
            timeout=int(timeout), time_created=self.time_manager.time()
        )

        # Signal the environment to enter wait for notification mode
        if self.wait_for_next_notification is not None:
            self.wait_for_next_notification()
