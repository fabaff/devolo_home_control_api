from .property import Property, WrongElementError
from ..backend.mprm_rest import MprmDeviceCommunicationError


class BinarySwitchProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid):
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise WrongElementError(f"{element_uid} is not a Binary Switch.")

        super().__init__(element_uid=element_uid)
        self.state = None


    def get_binary_switch_state(self) -> bool:
        """
        Update and return the binary switch state for the given uid.

        :param element_uid: element UID of the consumption. Usually starts with devolo.BinarySwitch
        :return: Binary switch state
        """
        response = self.mprm.extract_data_from_element_uid(self.element_uid)
        self.state = True if response.get("properties").get("state") == 1 else False
        return self.state

    def set_binary_switch(self, state: bool):
        """
        Set the binary switch of the given element_uid to the given state.

        :param element_uid: element_uid
        :param state: True if switching on, False if switching off
        """
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "turnOn" if state else "turnOff", []]}
        response = self.mprm.post(data)
        if response.get("result").get("status") == 2:
            raise MprmDeviceCommunicationError("The device is offline.")
        # TODO: Make this work again ;)
        # and not self._device_usable(get_device_uid_from_element_uid(element_uid)):
        if response.get("result").get("status") == 1:
            self.state = state
        else:
            self._logger.info(f"Could not set state of device {self.device_uid}. Maybe it is already at this state.")
            self._logger.info(f"Target state is {state}.Actual state is {self.state}.")
