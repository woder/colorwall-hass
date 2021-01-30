import http.client
import json
import logging
from types import SimpleNamespace
from .panel import Panel
from .panel import PanelEncoder
from . import effect
from .effect import EffectEncoder
from .effect import effectById

_LOGGER = logging.getLogger(__name__)


class API:

    def __init__(self, ip):
        self.ip = ip
        self.powered = False
        self.brightness = 255
        self.panels = []
        self.effectSettings = {}
        self.currentEffect = None

    def setPower(self, powered, brightness):
        conn = http.client.HTTPConnection(self.ip)
        state = {
            "power": powered,
            "brightness": brightness
        }
        payload = json.dumps(state)
        _LOGGER.debug("Set power: " + str(payload))
        headers = {
            'Content-Type': 'application/json'
        }
        conn.request("POST", "/power", payload, headers)
        res = conn.getresponse()
        if res.getcode() == http.HTTPStatus.OK:
            return True
        else:
            data = res.read()
            _LOGGER.error("Set panels returned an error: %s", data.decode("utf-8"))
            return False

    def getPower(self):
        conn = http.client.HTTPConnection(self.ip)
        payload = ''
        headers = {}
        conn.request("GET", "/power", payload, headers)
        res = conn.getresponse()
        data = res.read()
        x = json.loads(data.decode("utf-8"), object_hook=lambda d: SimpleNamespace(**d))
        return x

    def getPanels(self):
        conn = http.client.HTTPConnection(self.ip)
        payload = ''
        headers = {}
        conn.request("GET", "/panels", payload, headers)
        res = conn.getresponse()
        data = res.read()
        x = json.loads(data.decode("utf-8"), object_hook=lambda d: SimpleNamespace(**d))
        panels = []
        for p in x:
            panels.append(Panel(p.id, p.hue, p.saturation, p.brightness))

        return panels

    def setPanels(self, panels):
        """

        @type panels: list
        """
        conn = http.client.HTTPConnection(self.ip)
        payload = json.dumps(panels, cls=PanelEncoder)
        _LOGGER.debug("Set panels: " + str(payload))
        headers = {
            'Content-Type': 'application/json'
        }
        conn.request("POST", "/panels", payload, headers)
        res = conn.getresponse()
        if res.getcode() == http.HTTPStatus.OK:
            return True
        else:
            data = res.read()
            _LOGGER.error("Set panels returned an error: %s", data.decode("utf-8"))
            return False

    def getEffect(self):
        conn = http.client.HTTPConnection(self.ip)
        payload = ''
        headers = {}
        conn.request("GET", "/effect", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        x = json.loads(data.decode("utf-8"), object_hook=lambda d: SimpleNamespace(**d))
        if hasattr(x, 'settings'):
            return effectById(x.effect, x.settings)
        else:
            return effectById(x.effect, None)

    def setEffect(self, effecte):
        """
        @param effecte: Effect
        @return: boolean
        """

        conn = http.client.HTTPConnection(self.ip)
        payload = json.dumps(effecte, cls=EffectEncoder)
        _LOGGER.debug("Payload: " + str(payload))
        print(payload)
        headers = {
            'Content-Type': 'application/json'
        }
        conn.request("POST", "/effect", payload, headers)
        res = conn.getresponse()
        if res.getcode() == http.HTTPStatus.OK:
            return True
        else:
            data = res.read()
            _LOGGER.error("Set effect returned an error: %s", data.decode("utf-8"))
            return False

    @staticmethod
    def getEffectList():
        return effect.effects

    @staticmethod
    def getEffectIdByName(name):
        return effect.effectIdByName(name)

    @staticmethod
    def getEffectByName(name, settings):
        return effect.effectByName(name, settings)

    @staticmethod
    def validateConnection(ip):
        """Attempts to connect to the device to verify the given host"""
        try:
            conn = http.client.HTTPConnection(ip)
            payload = ''
            headers = {}
            conn.request("GET", "/power", payload, headers)
            res = conn.getresponse()
            if res.getcode() != http.HTTPStatus.OK:
                raise ColorWallConnectionError
        except OSError as err:
            raise ColorWallConnectionError from err

    def update(self):
        try:
            x = self.getPower()
            self.powered = x.power
            self.brightness = x.brightness
            self.panels = self.getPanels()
            self.currentEffect = self.getEffect()
        except OSError as err:
            raise ColorWallConnectionError from err


class ColorWallConnectionError(Exception):
    pass
