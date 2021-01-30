"""
ColorWall is an integration designed to interface with the ColorWall hardware project
"""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import API
from . import effect

DOMAIN = "color_wall"
PLATFORMS = ["light"]
CONTROLLER = "controller"
UNDO_UPDATE_LISTENER = "undo_update_listener"

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the ColorWall component"""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not entry.options:
        effects = {}
        for e in effect.effects:
            eId = effect.effectIdByName(e)
            eff = effect.data_schema[eId]
            vals = {}
            for key, value in eff.items():
                vals[str(key.schema)] = key.default()

            effects[eId] = vals

        _LOGGER.critical("Effects dict: " + str(effects))
        hass.config_entries.async_update_entry(
            entry, options=effects
        )

    if "host" in entry.data:
        hass.data[DOMAIN][entry.entry_id] = {
            CONTROLLER: API(entry.data["host"]),
            UNDO_UPDATE_LISTENER: entry.add_update_listener(update_listener)
        }

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the config entry"""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def fixDict(json_data) -> dict:
    """Converts JSON data created by hass back into the dict we expect
       Specifically, the string keys will become numeric if possible"""
    correctedDict = {}

    for key, value in json_data.items():
        if isinstance(value, list):
            value = [fixDict(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, dict):
            value = fixDict(value)
        try:
            key = int(key)
        except Exception as ex:
            pass
        correctedDict[key] = value

    return correctedDict


def remap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
