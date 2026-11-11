"""The half-built hall for the 2025 data-center pitch (variant of sc_datacenter)."""
from sc_datacenter import *
import sc_datacenter as _d


def build(variant=None):
    return _d.build("build")


MOVES = {"slow_push": _d.MOVES["slow_push"]}
