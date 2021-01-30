"""Platform for light integration."""
import logging
from typing import Any, Optional

from . import effect
from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import PlatformNotReady

from .api import ColorWallConnectionError
from .api import API
from . import DOMAIN, CONTROLLER, fixDict, remap

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_EFFECT, SUPPORT_BRIGHTNESS, ATTR_EFFECT, LightEntity,
    SUPPORT_COLOR, ATTR_HS_COLOR)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, config_entry: ConfigEntry, async_add_devices):
    """Add each light based on the passed data"""
    controller = hass.data[DOMAIN][config_entry.entry_id][CONTROLLER]

    options = fixDict(config_entry.options)
    for e in effect.effects:
        effc = effect.effectIdByName(e)
        if effc in options:
            sett = options[effc]
            if sett is not None:
                controller.effectSettings[effc] = (API.getEffectByName(e, sett))
            else:
                controller.effectSettings[effc] = (API.getEffectByName(e, effect.Settings({})))
        else:
            controller.effectSettings[effc] = (API.getEffectByName(e, effect.Settings({})))

    new_devices = await hass.async_add_executor_job(
        setup_main, controller
    )

    for p in controller.panels:
        new_devices.append(ColorWallPanel(controller, p.id))

    async_add_devices(new_devices, True)


def setup_main(controller) -> list:
    try:
        return [ColorWallMain(controller)]
    except ColorWallConnectionError as err:
        _LOGGER.warning("Cannot connect to host %s", controller.ip)
        raise PlatformNotReady() from err


class ColorWallMain(LightEntity):
    """Representation of an Awesome Light."""

    def __init__(self, controller):
        """
        @type controller: API
        @param controller: API
        """
        self._controller = controller
        self._controller.update()
        self._name = "ColorWall"
        self._unique_id = f"{self._controller.ip}-main"
        self._state = controller.powered
        self._brightness = 255  # todo update this to control master brightness
        self._effect = controller.currentEffect
        self._available = True
        self.sendInitial()  # send the initial settings so that changes are reflected immediately

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self) -> Optional[str]:
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if the entity is available"""
        return self._available

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def effect(self):
        """Returns the current effect"""
        return self._effect.name

    @property
    def effect_list(self):
        """Returns the list of available effects"""
        return self._controller.getEffectList()

    @property
    def supported_features(self):
        """Flag supported features"""
        return SUPPORT_BRIGHTNESS | SUPPORT_EFFECT

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        if ATTR_BRIGHTNESS in kwargs:
            self._controller.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
            self._brightness = self._controller.brightness

        if ATTR_EFFECT in kwargs:
            service = kwargs[ATTR_EFFECT]
            enumber = self._controller.getEffectIdByName(service)
            effecte = self._controller.getEffectByName(service,
                                                       self._controller.effectSettings[enumber].settings)
            self._controller.setEffect(effecte)
            self._effect = effecte

        self._controller.setPower(True, self.brightness)
        self._state = True

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._controller.setPower(False, self.brightness)
        self._state = False

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            self._controller.update()
            self._state = self._controller.powered
            self._brightness = self._controller.brightness
            self._effect = self._controller.currentEffect
            self._available = True
        except ColorWallConnectionError as err:
            _LOGGER.warning("Cannot connect to previously available host %s", self._controller.ip)
            self._available = False

    def sendInitial(self):
        if self._effect is not None:
            enumber = self._controller.getEffectIdByName(self._effect.name)
            effecte = self._controller.getEffectByName(self._effect.name,
                                                       self._controller.effectSettings[enumber].settings)
            self._controller.setEffect(effecte)


class ColorWallPanel(LightEntity):

    def __init__(self, controller, pid):
        """
        @type controller: API
        @param controller: API
        """
        self._controller = controller
        self._pid = pid
        self._panel = controller.panels[pid]
        self._unique_id = f"{self._controller.ip}-panel-{self._pid}"
        self._available = False

    @property
    def name(self):
        return "ColorWall Panel " + str(self._pid)

    @property
    def unique_id(self) -> Optional[str]:
        return self._unique_id

    @property
    def brightness(self):
        return self._panel.brightness

    @property
    def hs_color(self):
        return [
            remap(self._panel.hue, 0, 255, 0, 360),
            remap(self._panel.saturation, 0, 255, 0, 100)
        ]

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR

    @property
    def available(self) -> bool:
        return self._available

    @property
    def is_on(self) -> bool:
        return not self._panel.brightness == 0 and self._controller.powered

    def turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            self._panel.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        else:
            if self._panel.brightness == 0:
                self._panel.brightness = 255

        if ATTR_HS_COLOR in kwargs:
            self._panel.hue = remap(kwargs.get(ATTR_HS_COLOR, [0, 255])[0], 0, 360, 0, 255)
            self._panel.saturation = remap(kwargs.get(ATTR_HS_COLOR, [0, 255])[1], 0, 100, 0, 255)
        self._controller.panels[self._pid] = self._panel
        self._controller.setPanels(self._controller.panels)

    def turn_off(self, **kwargs: Any) -> None:
        self._panel.brightness = 0
        self._controller.panels[self._pid] = self._panel
        self._controller.setPanels(self._controller.panels)

    def update(self):
        try:
            self._controller.update()
            self._panel = self._controller.panels[self._pid]
            self._available = True
        except ColorWallConnectionError as err:
            _LOGGER.warning("Cannot connect to previously available host %s", self._controller.ip)
            self._available = False
