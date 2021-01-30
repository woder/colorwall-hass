# Effect class represents an effect
import json
from json import JSONEncoder
import voluptuous as vol


class Settings(object):
    def __init__(self, settings):
        self.__dict__.update(settings)

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def reprJSON(self):
        """Returns a dict that can be used to turn this object into its JSON form
           This function must be modified any time new class members are added to settings
           The only settings that should become JSON are the ones the firmware expects!
           Any extra settings will result in an out of memory exception on the device"""
        val = {}
        for key, value in self.__dict__.items():
            if key != "type":
                val[key] = value

        return val


class Effect:
    def __init__(self, effect, name, settings_schema):
        self.effect = effect
        self.name = name
        vals = {}
        for key, value in settings_schema.items():
            vals[str(key.schema)] = key.default()
        self.settings = Settings(vals)

    def reprJSON(self):
        """Returns a dict that can be used to turn this object into its JSON form
           This function must be modified any time new class members are added to effect
           or any of its sub classes"""
        val = {}
        for key, value in self.__dict__.items():
            if key != "name":
                val[key] = value

        return val


def effectById(effectId, settings):
    return {
        0: lambda sett: Smooth(sett.speed, sett.width),
        1: lambda sett: Bpm(sett.bpm, sett.style),
        2: lambda sett: Solid(),
        3: lambda sett: Colory(sett.speed),
        4: lambda sett: Wash(sett.speed, sett.baseHue, sett.deltaHue),
        5: lambda sett: Rainbow(sett.speed, sett.direction)
    }[effectId](settings)


def effectByName(effectName, settings):
    return {
        Smooth.name: lambda sett: Smooth(sett.speed, sett.width),
        Bpm.name: lambda sett: Bpm(sett.bpm, sett.style),
        Solid.name: lambda sett: Solid(),
        Colory.name: lambda sett: Colory(sett.speed),
        Wash.name: lambda sett: Wash(sett.speed, sett.baseHue, sett.deltaHue),
        Rainbow.name: lambda sett: Rainbow(sett.speed, sett.direction)
    }[effectName](settings)


def effectIdByName(effectName):
    return {
        Smooth.name: Smooth.eId,
        Bpm.name: Bpm.eId,
        Solid.name: Solid.eId,
        Colory.name: Colory.eId,
        Wash.name: Wash.eId,
        Rainbow.name: Rainbow.eId
    }[effectName]


class EffectEncoder(JSONEncoder):
    def default(self, o):
        if hasattr(o, "reprJSON"):
            return o.reprJSON()
        else:
            return json.JSONEncoder.default(self, o)


class Smooth(Effect):
    eId = 0
    name = "Smooth line of light"
    settings_schema = {
        vol.Optional("type", default="Smooth"): str,
        vol.Required("speed", default=2): int,
        vol.Required("width", default=10): int,
    }

    def __init__(self, speed, width):
        super().__init__(Smooth.eId, Smooth.name, Smooth.settings_schema)
        self.settings.speed = speed
        self.settings.width = width


class Bpm(Effect):
    eId = 1
    name = "Pulses of light"
    settings_schema = {
        vol.Optional("type", default="Bpm"): str,
        vol.Required("bpm", default=62): int,
        vol.Required("style", default=0): int,
    }

    def __init__(self, bpm, style):
        super().__init__(Bpm.eId, Bpm.name, Bpm.settings_schema)
        self.settings.bpm = bpm
        self.settings.style = style


class Solid(Effect):
    eId = 2
    name = "Solid light"
    settings_schema = {
    }

    def __init__(self):
        super().__init__(Solid.eId, Solid.name, Solid.settings_schema)


class Colory(Effect):
    eId = 3
    name = "Animated tile colors"
    settings_schema = {
        vol.Optional("type", default="Colory"): str,
        vol.Required("speed", default=2): int,
    }

    def __init__(self, speed):
        super().__init__(Colory.eId, Colory.name, Colory.settings_schema)
        self.settings.speed = speed


class Wash(Effect):
    eId = 4
    name = "Color wash"
    settings_schema = {
        vol.Optional("type", default="Wash"): str,
        vol.Required("speed", default=5): int,
        vol.Required("baseHue", default=0): int,
        vol.Required("deltaHue", default=16): int,
    }

    def __init__(self, speed, baseHue, deltaHue):
        super().__init__(Wash.eId, Wash.name, Wash.settings_schema)
        self.settings.speed = speed
        self.settings.baseHue = baseHue
        self.settings.deltaHue = deltaHue


class Rainbow(Effect):
    eId = 5
    name = "Animated rainbow"
    settings_schema = {
        vol.Optional("type", default="Rainbow"): str,
        vol.Required("speed", default=2): int,
        vol.Required("direction", default=0): int,
    }

    def __init__(self, speed, direction):
        super().__init__(Rainbow.eId, Rainbow.name, Rainbow.settings_schema)
        self.settings.speed = speed
        self.settings.direction = direction


effects = [
    Smooth.name,
    Bpm.name,
    Solid.name,
    Colory.name,
    Wash.name,
    Rainbow.name
]

data_schema = [
    Smooth.settings_schema,
    Bpm.settings_schema,
    Solid.settings_schema,
    Colory.settings_schema,
    Wash.settings_schema,
    Rainbow.settings_schema,
]

