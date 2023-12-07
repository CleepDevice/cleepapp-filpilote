#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.exception import MissingParameter, InvalidParameter, CommandError
from cleep.core import CleepModule
from cleep.common import CATEGORIES

class Filpilote(CleepModule):
    """
    Filpilote application
    """
    MODULE_AUTHOR = 'Cleep'
    MODULE_VERSION = '0.0.0'
    MODULE_DEPS = ['gpios']
    MODULE_DESCRIPTION = 'Control your home heaters using french fil-pilote way'
    MODULE_LONGDESCRIPTION = 'TODO'
    MODULE_TAGS = ['heater', 'pilote', 'fil', 'chauffage']
    MODULE_CATEGORY = CATEGORIES.HOMEAUTOMATION
    MODULE_URLINFO = 'https://github.com/CleepDevice/cleepapp-filpilote'
    MODULE_URLHELP = 'https://github.com/CleepDevice/cleepapp-filpilote/wiki'
    MODULE_URLSITE = 'https://fr.wikipedia.org/wiki/Chauffage_%C3%A9lectrique#Fil_pilote'
    MODULE_URLBUGS = 'https://github.com/CleepDevice/cleepapp-filpilote/issues'
    MODULE_COUNTRY = 'FR'
    MODULE_LABEL = 'Fil-pilote'

    MODULE_CONFIG_FILE = 'filpilote.conf'
    DEFAULT_CONFIG = {}

    MODE_ANTIFROST = "ANTIFROST"
    MODE_COMFORT = "COMFORT"
    MODE_ECO = "ECO"
    MODE_STOP = "STOP"
    MODES = [MODE_ANTIFROST, MODE_COMFORT, MODE_ECO, MODE_STOP]

    MODE_CONFIGS = {
        "ANTIFROST": {
            "gpio1": True,
            "gpio2": False,
        },
        "COMFORT": {
            "gpio1": False,
            "gpio2": False,
        },
        "ECO": {
            "gpio1": True,
            "gpio2": True,
        },
        "STOP": {
            "gpio1": False,
            "gpio2": True,
        },
    }

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled: debug status
        """
        CleepModule.__init__(self, bootstrap, debug_enabled)

    def _configure(self):
        """
        Configure module.
        Use this function to configure your variables and local stuff that is not blocking.
        At this time other applications are not started and all your command requests will fail.
        """
        pass

    def _on_start(self):
        """
        Start module.
        Use this function to start your tasks.
        At this time all applications are started and should respond to your command requests.
        """
        pass

    def _on_stop(self):
        """
        Stop module
        Use this function to stop your tasks and close your external connections.
        """
        pass

    def on_event(self, event):
        """
        Event received

        Args:
            event (MessageRequest): event data
        """
        # execute here actions when you receive a specific event:
        #  - on time event => cron task
        #  - on alert event => send email or push message
        #  - ...
        pass

    def __get_area_by_name(self, area_name):
        """
        Return specified area

        Args:
            area_name (str): area name

        Returns:
            dict: area if found
            None: if area not found
        """
        devices = self._get_devices()
        found = list(filter(lambda dev: dev['name'] == area_name, devices.values()))
        return found[0] if len(found) == 1 else None
    
    def __get_assigned_gpios(self):
        """
        Return list of assigned gpios
        """
        resp = self.send_command("get_assigned_gpios", "gpios")
        if resp.error:
            self.logger.error(resp.message)
            return []

        return resp.data

    def add_area(self, area_name, gpio1, gpio2):
        """
        Add area. Typically ground floors heaters are separated from floor heaters, an area controls one fil-pilote line.

        Args:
            area_name (str): name of area
            gpio1 (str): first gpio name
            gpio2 (str): second gpio name

        Returns:
            dict: created area::

            {
                area_name (str): name of area
                gpio1 (str): gpio1
                gpio2 (str): gpio2
                mode (str): area mode (STOP)
                uuid (str): device uuid
            }

        """
        assigned_gpios = self.__get_assigned_gpios()
        self._check_parameters([
            {
                'name': 'area_name',
                'value': area_name,
                'type': str,
                'validator': lambda val: self.__get_area_by_name(val) is None,
                'message': 'Area name is already in use'
            },
            {
                'name': 'gpio1',
                'value': gpio1,
                'type': str,
                'validator': lambda val: val not in assigned_gpios,
                'message': 'Gpio1 is already used by another device'
            },
            {
                'name': 'gpio2',
                'value': gpio2,
                'type': str,
                'validator': lambda val: val not in assigned_gpios,
                'message': 'Gpio2 is already used by another device'
            }
        ])

        area = {
            'type': 'filpilotearea',
            'name': area_name,
            'mode': self.MODE_STOP,
        }

        # save gpios
        gpio1_data = self.__save_gpio_in_gpios(area_name, gpio1, 1, area)
        gpio2_data = self.__save_gpio_in_gpios(area_name, gpio2, 2, area)

        # save area
        area.update({
            'gpio1': gpio1_data,
            'gpio2': gpio2_data
        })
        added_area = self._add_device(area)
        if added_area is None:
            self.__delete_gpio_in_gpios(gpio1_data, 1)
            self.__delete_gpio_in_gpios(gpio2_data, 2)
            raise CommandError('Unable to save new area')
               
    def delete_area(self, area_uuid):
        """
        Delete specified area
        
        Args:
            area_uuid (str): area uuid

        Returns:
            bool: True if area deleted successfully, False otherwise
        """
        self._check_parameters([
            {
                'name': 'area_uuid',
                'value': area_uuid,
                'type': str,
                'validator': lambda uuid: self._get_device(uuid) is not None,
                'message': 'Specified area does not exist'
            }
        ])
        
        area = self._get_device(area_uuid)

        # delete gpios
        self.__delete_gpio_in_gpios(area['gpio1'], 1)
        self.__delete_gpio_in_gpios(area['gpio2'], 2)

        # delete area
        if not self._delete_device(area['uuid']):
            raise CommandError('Unable to delete area')
        
        return True

    def set_mode(self, area_uuid, mode):
        """
        Set area mode

        Args:
            area_uuid (str): area uuid
            mode (str): new mode

        Returns:
            bool: True if mode set sucessfully
        """
        self._check_parameters([
            {
                'name': 'area_uuid',
                'value': area_uuid,
                'type': str,
                'validator': lambda uuid: self._get_device(uuid) is not None,
                'message': 'Specified area does not exist'
            },
            {
                'name': 'mode',
                'value': mode,
                'type': str,
                'validator': lambda val: val in self.MODES,
                'message': 'Specified mode does not exist'
            }
        ])

        area = self._get_device(area_uuid)
        if not self._update_device(area['uuid'], { 'mode': mode }):
            raise CommandError(f'Unable to set mode {mode} for {area["name"]}')
    
        return self.__apply_mode(mode, area)
    
    def __apply_mode(self, mode, area):
        """
        Apply specified mode for area

        Args:
            mode (str): mode to apply
            area (dict): area object

        Returns:
            bool: True if mode applied successfully
        """
        mode_config = self.MODE_CONFIGS[mode]

        gpio_command = 'turn_on' if mode_config['gpio1'] else 'turn_off'
        gpio_uuid = area['gpio1']['uuid']
        resp1 = self.send_command(gpio_command, 'gpios', { 'device_uuid': gpio_uuid })
        if resp1.error:
            self.logger.error('Error executing "%s" command for gpio1 "%s" from area "%s"', gpio_command, gpio_uuid, area['name'])

        gpio_command = 'turn_on' if mode_config['gpio2'] else 'turn_off'
        gpio_uuid = area['gpio2']['uuid']
        resp2 = self.send_command(gpio_command, 'gpios', { 'device_uuid': gpio_uuid })
        if resp2.error:
            self.logger.error('Error executing "%s" command for gpio1 "%s" from area "%s"', gpio_command, gpio_uuid, area['name'])

        if not resp1.error and not resp2.error:
            self.logger.info('Mode "%s" applying for area "%s"', mode, area['name'])

    def __save_gpio_in_gpios(self, area_name, gpio, gpio_index, area):
        """
        Save gpio in gpios app

        Args:
            area_name (str): area name
            gpio (str): gpio
            gpio_index (number): gpio index (1 or 2)
            area (dict): current area data. Used to delete previous gpio if error occured
        """
        data = {
            'name': f'filpilote_{area_name}_gpio{gpio_index}',
            'gpio': gpio,
            'mode': 'output',
            'keep': True,
            'inverted': False,
        }
        
        resp = self.send_command('add_gpio', 'gpios', data)
        if resp.error:
            if area['gpio1']:
                self.__delete_gpio_in_gpios(area['gpio1'], 1)
            raise CommandError(f'Error saving gpio{gpio_index} configuration')
        
        return resp.data
    
    def __delete_gpio_in_gpios(self, gpio, gpio_index):
        """
        Delete specified gpio in gpios app

        Args:
            gpio (dict): gpio data as returned by gpios app
            gpio_index (number): area gpio index

        Returns:
            bool: True if gpio deleted successfully
        """
        resp = self.send_command('delete_gpio', 'gpios', { 'device_uuid': gpio['uuid'] })
        if resp.error:
            self.logger.warn('Error deleting gpio%s "%s" on gpios app', gpio_index, gpio['uuid'])
            return False
        return True