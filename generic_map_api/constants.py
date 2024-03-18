from enum import Enum

WGS84 = 4326


class ViewportHandling(Enum):
    TILES = "tiles"
    SPLIT = "split"
    SINGLE = "single"
