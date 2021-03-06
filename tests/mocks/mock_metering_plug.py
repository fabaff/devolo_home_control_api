import json
import pathlib

import requests

from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty
from devolo_home_control_api.properties.consumption_property import ConsumptionProperty
from devolo_home_control_api.properties.multi_level_sensor_property import MultiLevelSensorProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

from .mock_gateway import MockGateway


def metering_plug(device_uid: str) -> Zwave:
    """
    Represent a metering plug in tests

    :param device_uid: Device UID this mock shall have
    :return: Metering Plug device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    mydevolo = Mydevolo()
    device = Zwave(mydevolo_instance=mydevolo, **test_data['devices']['mains']['properties'])
    gateway = MockGateway(test_data['gateway']['id'], mydevolo=mydevolo)
    session = requests.Session()

    device.binary_switch_property = {}
    device.consumption_property = {}
    device.multi_level_sensor_property = {}
    device.settings_property = {}

    device.binary_switch_property[f'devolo.BinarySwitch:{device_uid}'] = \
        BinarySwitchProperty(gateway=gateway,
                             session=session,
                             mydevolo=mydevolo,
                             element_uid=f"devolo.BinarySwitch:{device_uid}",
                             state=test_data['devices']['mains']['properties']['state'],
                             enabled=test_data['devices']['mains']['properties']['guiEnabled'])
    device.consumption_property[f'devolo.Meter:{device_uid}'] = \
        ConsumptionProperty(gateway=gateway,
                            session=session,
                            mydevolo=mydevolo,
                            element_uid=f"devolo.Meter:{device_uid}",
                            current=test_data['devices']['mains']['properties']['current_consumption'],
                            total=test_data['devices']['mains']['properties']['total_consumption'],
                            total_since=test_data['devices']['mains']['properties']['sinceTime'])
    device.multi_level_sensor_property[f'devolo.VoltageMultiLevelSensor:{device_uid}'] = \
        MultiLevelSensorProperty(gateway=gateway,
                                 session=session,
                                 mydevolo=mydevolo,
                                 element_uid=f"devolo.VoltageMultiLevelSensor:{device_uid}",
                                 current=test_data['devices']['mains']['properties']['voltage'])
    device.settings_property["param_changed"] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         mydevolo=mydevolo,
                         element_uid=f"cps.{device_uid}")
    device.settings_property['general_device_settings'] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         mydevolo=mydevolo,
                         element_uid=f"gds.{device_uid}",
                         events_enabled=test_data['devices']['mains']['properties']['eventsEnabled'],
                         icon=test_data['devices']['mains']['properties']['icon'],
                         name=test_data['devices']['mains']['properties']['itemName'],
                         zone_id=test_data['devices']['mains']['properties']['zoneId'])
    device.settings_property["led"] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         mydevolo=mydevolo,
                         element_uid=f"lis.{device_uid}",
                         led_setting=test_data['devices']['mains']['properties']['led_setting'])
    device.settings_property["protection"] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         mydevolo=mydevolo,
                         element_uid=f"ps.{device_uid}",
                         local_switching=test_data['devices']['mains']['properties']['local_switch'],
                         remote_switching=test_data['devices']['mains']['properties']['remote_switch'])

    return device
