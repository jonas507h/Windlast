def gesamtgewicht(konstruktion) -> float:
    """
    Summiert das Gewicht aller Kinder, die eine .gewicht() Methode besitzen.
    Neutral gegenüber verschiedenen Konstruktionstypen.
    """
    total = 0.0
    # typische Sammlungen – erweitern wir bei Bedarf
    for attr in ("bodenplatten", "traversen", "elemente", "komponenten"):
        children = getattr(konstruktion, attr, [])
        for child in children or []:
            if hasattr(child, "gewicht") and callable(child.gewicht):
                total += float(child.gewicht())
    return total
