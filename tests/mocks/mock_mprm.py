from devolo_home_control_api.backend.mprm_websocket import MprmWebsocket


class MockMprm(MprmWebsocket):
    def __init__(self, mydevolo_instance):
        super(MprmWebsocket, self).__init__(mydevolo_instance=mydevolo_instance)
