"""Initial navigation for the Caronte user application."""

from __future__ import annotations

from enum import Enum

from ..application.configuration import ConfigurationService


class UserRoute(str, Enum):
    FIRST_RUN = "first_run"
    HOME = "home"
    ACTIVITY = "activity"
    SETTINGS = "settings"


def initial_route(configuration: ConfigurationService) -> UserRoute:
    """Choose the first user screen without coupling navigation to storage."""

    return UserRoute.HOME if configuration.exists() else UserRoute.FIRST_RUN
