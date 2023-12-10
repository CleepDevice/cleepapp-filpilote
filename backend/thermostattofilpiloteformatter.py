#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.thermostatprofile import ThermostatProfile


class ThermostatToFilPiloteFormatter(ProfileFormatter):
    """
    Thermostat event data to ThermostatProfile
    """

    def __init__(self, params):
        """
        Constuctor

        Args:
            params (dict): formatter parameters
        """
        ProfileFormatter.__init__(
            self, params, "thermostat.set.mode", ThermostatProfile()
        )

    def _fill_profile(self, event_params, profile):
        """
        Fill profile with event data

        Args:
            event_params (dict): event parameters
            profile (Profile): profile instance
        """
        if event_params["mode"] in ["comfort1", "comfort2", "comfort3"]:
            profile.mode = ThermostatProfile.COMFORT1
        elif event_params["mode"] == "stop":
            profile.mode = ThermostatProfile.STOP
        elif event_params["mode"] == "antifrost":
            profile.mode = ThermostatProfile.ANTIFROST
        elif event_params["mode"] == "eco":
            profile.mode = ThermostatProfile.ECO

        return profile
