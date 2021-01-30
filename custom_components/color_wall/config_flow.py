from typing import Dict, Any, Optional
from homeassistant import config_entries
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from . import DOMAIN, fixDict
from . import effect
from .api import API, ColorWallConnectionError

EFFECT_TO_CONFIGURE = "effect_to_configure"
CONFIG_ALL = "Configure all effects"


@config_entries.HANDLERS.register(DOMAIN)
class ColorWallConfigFlow(config_entries.ConfigFlow):
    """ColorWall config flow"""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handles the initial configure step"""
        errors = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    API.validateConnection,
                    user_input["host"]
                )
            except ColorWallConnectionError:
                errors["base"] = "cannot_connect"

            if "base" not in errors:
                await self.async_set_unique_id(user_input["host"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input["host"],
                    data={
                        "host": user_input["host"]
                    }
                )

        data_schema = {
            vol.Required("host"): str
        }

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "OptionsFlow":
        """Get the options flow for this handler"""
        return ColorWallOptionsFlowHandler(config_entry)


class ColorWallOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for ColorWall"""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry
        self.step = 0
        self.values = {}
        if not self.config_entry.options:
            self.vals = fixDict(self.config_entry.options)
        else:
            self.vals = {}

    async def async_step_init(self, user_input=None):
        """Handle the options flow"""
        if user_input is not None:
            if user_input[EFFECT_TO_CONFIGURE] == CONFIG_ALL:
                return await self.async_step_all()
            else:
                self.step = effect.effectIdByName(user_input[EFFECT_TO_CONFIGURE])
                return await self.async_step_effect()

        list = effect.effects.copy()
        list.append(CONFIG_ALL)
        data = {
            vol.Required(EFFECT_TO_CONFIGURE): vol.In(list)
        }
        return self.async_show_form(step_id="init", data_schema=vol.Schema(data))

    async def async_step_all(self, user_input=None):
        """Handle the configure all effects flow"""
        if user_input is not None:
            self.values[self.step] = user_input
            self.step = self.step + 1

        if self.step == len(effect.data_schema):
            return self.async_create_entry(
                title="ColorWall",
                data={
                    "options": self.values
                })

        if len(effect.data_schema[self.step]) == 0:
            self.step = self.step + 1
            if self.step < len(effect.data_schema):
                return await self.async_step_all(None)

        data = effect.data_schema[self.step]
        if self.step in self.vals:
            for key, value in data.items():
                if str(key.schema) != "type":
                    key.default = vol.default_factory(self.vals[self.step][str(key.schema)])

        return self.async_show_form(step_id="all", data_schema=vol.Schema(data))

    async def async_step_effect(self, user_input=None):
        """Handle the configure single effect flow"""
        if user_input is not None:
            changed = self.vals
            changed[self.step] = user_input
            return self.async_create_entry(
                title="ColorWall",
                data={
                    "options": changed
                })

        data = effect.data_schema[self.step]
        if self.step in self.vals:
            for key, value in data.items():
                if str(key.schema) != "type":
                    key.default = vol.default_factory(self.vals[self.step][str(key.schema)])
        return self.async_show_form(step_id="effect", data_schema=vol.Schema(data))
