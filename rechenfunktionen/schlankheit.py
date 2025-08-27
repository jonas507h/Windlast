def schlankheit(laenge: float, hoehe: float) -> float:
    """Einfaches Verhältnis λ = laenge / hoehe."""
    if laenge <= 0 or hoehe <= 0:
        raise ValueError("laenge und hoehe müssen > 0 sein.")
    return laenge / hoehe
