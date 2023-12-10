#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import logging
import sys

sys.path.append("../")
from backend.filpilote import Filpilote
from cleep.exception import (
    InvalidParameter,
    CommandError,
)
from cleep.libs.tests import session
from mock import Mock, patch


class TestFilpilote(unittest.TestCase):
    GPIO1 = {
        "uuid": "814c9416-cdb7-4a8d-b52c-21bfa87f86f2",
        "name": "gpio1",
        "gpio": "GPIO1",
        "mode": "output",
        "type": "gpio",
        "subtype": "output",
        "pin": 1,
    }
    GPIO2 = {
        "uuid": "814c9416-cdb7-4a8d-b52c-21bfa87f86f4",
        "name": "gpio2",
        "gpio": "GPIO2",
        "mode": "output",
        "type": "gpio",
        "subtype": "output",
        "pin": 2,
    }

    def setUp(self):
        # Change here logging.DEBUG to logging.FATAL to disable logging during tests writings
        # Note that coverage command does not display logging
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        self.session = session.TestSession(self)

    def tearDown(self):
        # clean session
        self.session.clean()

    def init(self, start=True):
        """
        Call this function at beginning of every test cases. By default it starts your app, but if you specify start=False,
        the application must be started manually which is useful in some cases like testing _on_configure app function.
        """
        # next line instanciates your module, overwriting all useful stuff to isolate your module for tests
        self.module = self.session.setup(Filpilote)

        add_gpio_mock = self.session.make_mock_command(
            "add_gpio", [self.GPIO1, self.GPIO2]
        )
        self.session.add_mock_command(add_gpio_mock)
        delete_gpio_mock = self.session.make_mock_command("delete_gpio")
        self.session.add_mock_command(delete_gpio_mock)
        turn_on_mock = self.session.make_mock_command("turn_on")
        self.session.add_mock_command(turn_on_mock)
        turn_off_mock = self.session.make_mock_command("turn_off")
        self.session.add_mock_command(turn_off_mock)
        get_assigned_gpios_mock = self.session.make_mock_command(
            "get_assigned_gpios", ["GPIO3"]
        )
        self.session.add_mock_command(get_assigned_gpios_mock)

        if start:
            self.session.start_module(self.module)

    def test_add_area(self):
        self.init()
        self.module._add_device = Mock()

        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")
        logging.debug("Created area: %s", area)

        self.module._add_device.assert_called_once_with(
            {
                "type": "filpilotearea",
                "name": "firstfloor",
                "mode": Filpilote.MODE_STOP,
                "gpio1": self.GPIO1,
                "gpio2": self.GPIO2,
            }
        )
        self.session.assert_command_called_with(
            "add_gpio",
            {
                "name": "filpilote_firstfloor_gpio1",
                "gpio": "GPIO1",
                "mode": "output",
                "keep": True,
                "inverted": False,
            },
        )
        self.session.assert_command_called_with(
            "add_gpio",
            {
                "name": "filpilote_firstfloor_gpio2",
                "gpio": "GPIO2",
                "mode": "output",
                "keep": True,
                "inverted": False,
            },
        )
        self.assertDictEqual(
            area,
            {
                "type": "filpilotearea",
                "name": "firstfloor",
                "mode": Filpilote.MODE_STOP,
                "gpio1": self.GPIO1,
                "gpio2": self.GPIO2,
            },
        )

    def test_add_area_should_delete_gpio1_gpio2_if_add_device_failed(self):
        self.init()
        self.module._add_device = Mock(return_value=None)

        with self.assertRaises(CommandError) as cm:
            self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        self.assertEqual(cm.exception.message, "Unable to save new area")
        self.session.assert_command_called_with(
            "delete_gpio", {"device_uuid": self.GPIO1["uuid"]}
        )
        self.session.assert_command_called_with(
            "delete_gpio", {"device_uuid": self.GPIO2["uuid"]}
        )

    def test_add_area_should_delete_gpio1_if_gpio2_reservation_failed(self):
        self.init()
        self.session.set_mock_command_response(
            "add_gpio", [self.GPIO1, session.CommandFailure("Error GPIO2")]
        )
        self.module._add_device = Mock()

        with self.assertRaises(CommandError) as cm:
            self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        self.assertEqual(cm.exception.message, "Error GPIO2")
        self.session.assert_command_called_with(
            "delete_gpio", {"device_uuid": self.GPIO1["uuid"]}
        )
        self.module._add_device.assert_not_called()

    def test_add_area_name_already_used(self):
        self.init()

        self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_area("firstfloor", "GPIO1", "GPIO2")
        self.assertEqual(cm.exception.message, "Area name is already in use")

    def test_delete_area(self):
        self.init()
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")
        logging.debug("Created area %s", area)

        response = self.module.delete_area(area["uuid"])
        logging.debug("Response: %s", response)

        self.assertTrue(response)
        self.session.assert_command_called_with(
            "delete_gpio", {"device_uuid": self.GPIO1["uuid"]}
        )
        self.session.assert_command_called_with(
            "delete_gpio", {"device_uuid": self.GPIO2["uuid"]}
        )

    def test_delete_area_unknown_area_name(self):
        self.init()

        with self.assertRaises(InvalidParameter) as cm:
            self.module.delete_area("a-uuid")
        self.assertEqual(cm.exception.message, "Specified area does not exist")

    def test_delete_area_should_not_failed_if_gpio_deletion_failed(self):
        self.init()
        self.session.set_mock_command_failed("delete_gpio")
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        response = self.module.delete_area(area["uuid"])
        logging.debug("Response: %s", response)

        self.assertTrue(response)

    def test_delete_area_should_throw_error_if_area_deletion_failed(self):
        self.init()
        self.module._delete_device = Mock(return_value=False)
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        with self.assertRaises(CommandError) as cm:
            self.module.delete_area(area["uuid"])
        self.assertEqual(cm.exception.message, "Unable to delete area")

    def test_set_mode_eco(self):
        self.init()
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        response = self.module.set_mode(area["uuid"], self.module.MODE_ECO)

        self.assertTrue(response)
        device = self.module._get_device(area["uuid"])
        self.assertEqual(device["mode"], self.module.MODE_ECO)
        self.session.assert_command_called_with(
            "turn_on", {"device_uuid": self.GPIO1["uuid"]}
        )
        self.session.assert_command_called_with(
            "turn_on", {"device_uuid": self.GPIO2["uuid"]}
        )

    def test_set_mode_antifrost(self):
        self.init()
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        response = self.module.set_mode(area["uuid"], self.module.MODE_ANTIFROST)

        self.assertTrue(response)
        device = self.module._get_device(area["uuid"])
        self.assertEqual(device["mode"], self.module.MODE_ANTIFROST)
        self.session.assert_command_called_with(
            "turn_on", {"device_uuid": self.GPIO1["uuid"]}
        )
        self.session.assert_command_called_with(
            "turn_off", {"device_uuid": self.GPIO2["uuid"]}
        )

    def test_set_mode_comfort(self):
        self.init()
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        response = self.module.set_mode(area["uuid"], self.module.MODE_COMFORT)

        self.assertTrue(response)
        device = self.module._get_device(area["uuid"])
        self.assertEqual(device["mode"], self.module.MODE_COMFORT)
        self.session.assert_command_called_with(
            "turn_off", {"device_uuid": self.GPIO1["uuid"]}
        )
        self.session.assert_command_called_with(
            "turn_off", {"device_uuid": self.GPIO2["uuid"]}
        )

    def test_set_mode_stop(self):
        self.init()
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        response = self.module.set_mode(area["uuid"], self.module.MODE_STOP)

        self.assertTrue(response)
        device = self.module._get_device(area["uuid"])
        self.assertEqual(device["mode"], self.module.MODE_STOP)
        self.session.assert_command_called_with(
            "turn_off", {"device_uuid": self.GPIO1["uuid"]}
        )
        self.session.assert_command_called_with(
            "turn_on", {"device_uuid": self.GPIO2["uuid"]}
        )

    def test_set_mode_invalid_params(self):
        self.init()

        with self.assertRaises(InvalidParameter) as cm:
            self.module.set_mode("an.uuid", self.module.MODE_ECO)
        self.assertEqual(cm.exception.message, "Specified area does not exist")

        self.module._get_device = Mock(return_value={})
        with self.assertRaises(InvalidParameter) as cm:
            self.module.set_mode("an.uuid", "amode")
        self.assertEqual(cm.exception.message, "Specified mode does not exist")

    def test_set_mode_update_device_failed_should_raise_exception(self):
        self.init()
        self.module._update_device = Mock(return_value=False)
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")

        with self.assertRaises(CommandError) as cm:
            self.module.set_mode(area["uuid"], self.module.MODE_ECO)

        self.assertEqual(
            cm.exception.message, f"Unable to set mode ECO for {area['name']}"
        )

    def test_set_mode_return_false_if_gpio1_attribution_failed_and_restore_previous_mode(
        self,
    ):
        self.init()
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")
        self.session.set_mock_command_failed("turn_on")

        response = self.module.set_mode(area["uuid"], self.module.MODE_ECO)

        self.assertFalse(response)
        device = self.module._get_device(area["uuid"])
        self.assertEqual(device["mode"], area["mode"])

    def test_set_mode_return_false_if_gpio2_attribution_failed_and_restore_previous_mode(
        self,
    ):
        self.init()
        area = self.module.add_area("firstfloor", "GPIO1", "GPIO2")
        self.session.set_mock_command_response(
            "turn_on", ["ok", Exception("GPIO2 failed")]
        )

        response = self.module.set_mode(area["uuid"], self.module.MODE_ECO)

        self.assertFalse(response)
        device = self.module._get_device(area["uuid"])
        self.assertEqual(device["mode"], area["mode"])


# do not remove code below, otherwise tests won't run
if __name__ == "__main__":
    unittest.main()
