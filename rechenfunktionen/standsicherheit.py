from standsicherheit_utils import generiere_windrichtungen

def kippsicherheit(konstruktion) -> float:
    for winkel, richtung in generiere_windrichtungen(anzahl=4):
        pass
    return 1.0  # TODO: echte Formel

def gleitsicherheit(konstruktion) -> float:
    return 1.0  # TODO

def abhebesicherheit(konstruktion) -> float:
    return 1.0  # TODO
