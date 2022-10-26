from os import path

with open(path.join(path.dirname(__file__), "VERSION"), encoding="utf-8") as f:
    __version__ = f.read().strip()

__author__ = "Skytek Ltd."
__author_website__ = "https://skytek.com"
