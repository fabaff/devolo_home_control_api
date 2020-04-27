import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.multi_level_sensor_property import MultiLevelSensorProperty


@pytest.mark.usefixtures("home_control_instance")
class TestMultiLevelSensorProperty:
    def test_multi_level_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            MultiLevelSensorProperty(gateway=gateway_instance,
                                     session=mprm_session,
                                     element_uid="invalid",
                                     value=0.0,
                                     unit="%")
