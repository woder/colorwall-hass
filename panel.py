# A light panel
# has an ID, a hue, and a brightness
from collections import namedtuple
from json import JSONEncoder


class Panel:
    def __init__(self, id, hue, sat, brightness):
        self.id = id
        self.hue = hue
        self.saturation = sat
        self.brightness = brightness


class PanelEncoder(JSONEncoder):
    def default(self, o): return o.__dict__
