from enum import Enum


class RuntimeMode(str, Enum):
    LOCAL = "local"
    SERVER = "server"