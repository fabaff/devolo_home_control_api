import json
import threading
import time

import websocket
from requests import ConnectionError
from urllib3.connection import ConnectTimeoutError

from ..exceptions.gateway import GatewayOfflineError
from ..mydevolo import Mydevolo
from .mprm_rest import MprmRest


class MprmWebsocket(MprmRest):
    """
    The abstract MprmWebsocket object handles calls to the mPRM via websockets. It does not cover all API calls, just those
    requested up to now. All calls are done in a gateway context, so you have to create a derived class, that provides a
    Gateway object and a Session object. Further, the derived class needs to implement methods to connect to the websocket,
    either local or remote. Last but not least, the derived class needs to implement a method that is called on new messages.

    The websocket connection itself runs in a thread, that might not terminate as expected. Using a with-statement is
    recommended.

    :param mydevolo_instance: Mydevolo instance for talking to the devolo Cloud
    """

    def __init__(self, mydevolo_instance: Mydevolo):
        super().__init__(mydevolo_instance)
        self._ws: websocket.WebSocketApp = None
        self._connected = False     # This attribute saves, if the websocket is fully established
        self._reachable = True      # This attribute saves, if the a new session can be established
        self._event_sequence = 0

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.websocket_disconnect()


    def get_local_session(self):
        raise NotImplementedError(f"{self.__class__.__name__} needs a method to connect locally to a gateway.")

    def get_remote_session(self):
        raise NotImplementedError(f"{self.__class__.__name__} needs a method to connect remotely to a gateway.")

    def on_update(self, message):
        raise NotImplementedError(f"{self.__class__.__name__} needs a method to process messages from the websocket.")

    def wait_for_websocket_establishment(self):
        """
        In some cases it is needed to wait for the websocket to be fully established. This method can be used to block your
        current thread for up to one minute.
        """
        start_time = time.time()
        while not self._connected and time.time() < start_time + 600:
            time.sleep(0.1)
        if not self._connected:
            self._logger.debug("Websocket could not be established")
            raise GatewayOfflineError("Websocket could not be established.")

    def websocket_connect(self):
        """
        Set up the websocket connection. The protocol type of the known session URL is exchanged depending on whether TLS is
        used or not. After establishing the websocket, a ping is sent every 30 seconds to keep the connection alive. If there
        is no response within 5 seconds, the connection is terminated with error state.
        """
        ws_url = self._session.url.replace("https://", "wss://").replace("http://", "ws://")
        cookie = "; ".join([str(name) + "=" + str(value) for name, value in self._session.cookies.items()])
        ws_url = f"{ws_url}/remote/events/?topics=com/prosyst/mbs/services/fim/FunctionalItemEvent/PROPERTY_CHANGED," \
                 f"com/prosyst/mbs/services/fim/FunctionalItemEvent/UNREGISTERED" \
                 f"&filter=(|(GW_ID={self.gateway.id})(!(GW_ID=*)))"
        self._logger.debug(f"Connecting to {ws_url}")
        self._ws = websocket.WebSocketApp(ws_url,
                                          cookie=cookie,
                                          on_open=self._on_open,
                                          on_message=self._on_message,
                                          on_error=self._on_error,
                                          on_close=self._on_close,
                                          on_pong=self._on_pong,
                                          header={"Connection": "Upgrade"})
        self._ws.run_forever(ping_interval=30, ping_timeout=5)

    def websocket_disconnect(self, event: str = ""):
        """
        Close the websocket connection.
        """
        self._logger.info("Closing web socket connection.")
        if event:
            self._logger.info(f"Reason: {event}")
        self._ws.close()


    def _on_close(self):
        """ Callback method to react on closing the websocket. """
        self._logger.info("Closed web socket connection.")

    def _on_error(self, error: Exception):
        """ Callback method to react on errors. We will try reconnecting with prolonging intervals. """
        self._logger.exception(error)
        self._connected = False
        self._reachable = False
        self._ws.close()
        self._event_sequence = 0

        sleep_interval = 16
        while not self._reachable:
            self._try_reconnect(sleep_interval)
            sleep_interval = sleep_interval * 2 if sleep_interval < 2048 else 3600

        self.websocket_connect()

    def _on_message(self, message: str):
        """ Callback method to react on a message. """
        msg = json.loads(message)
        self._logger.debug(f"Got message from websocket:\n{msg}")
        event_sequence = msg["properties"]["com.prosyst.mbs.services.remote.event.sequence.number"]
        if event_sequence == self._event_sequence:
            self._event_sequence += 1
        else:
            self._logger.warning(f"We missed a websocket message. Internal event_sequence is at {self._event_sequence}. "
                                 f"Event sequence by websocket is at {event_sequence}")
            self._event_sequence = event_sequence + 1
            self._logger.debug(f"self._event_sequence is set to {self._event_sequence}")

        self.on_update(msg)

    def _on_open(self):
        """ Callback method to keep the websocket open. """
        def run():
            self._logger.info("Starting web socket connection.")
            while self._ws.sock is not None and self._ws.sock.connected:
                time.sleep(1)
        threading.Thread(target=run, name=f"{__class__.__name__}.websocket_run").start()
        self._connected = True

    def _on_pong(self, *args):
        """ Callback method to keep the session valid. """
        self.refresh_session()

    def _try_reconnect(self, sleep_interval: int):
        """ Try to reconnect to the websocket. """
        try:
            self._logger.info("Trying to reconnect to the websocket.")
            # TODO: Check if local_ip is still correct after lost connection
            self.get_local_session() if self._local_ip else self.get_remote_session()
            self._reachable = True
        except (json.JSONDecodeError, ConnectTimeoutError, ConnectionError, GatewayOfflineError):
            self._logger.info(f"Sleeping for {sleep_interval} seconds.")
            time.sleep(sleep_interval)
