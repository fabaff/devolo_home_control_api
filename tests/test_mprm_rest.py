from devolo_home_control_api.mprm_rest import MprmRest


class TestMprmRest:
    def test_binary_switch_devices(self, mock_gateway, mock_inspect_devices, mock_mprmrest__detect_gateway_in_lan):
        MprmRest("1409301750000598")
