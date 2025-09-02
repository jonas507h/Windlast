from datenstruktur.enums import ObjektTyp
from rechenfunktionen import Vec3
from bauelemente.traversenstrecke import Traversenstrecke

def main():
    # 8 m waagerecht (x-Achse), Orientierung nach oben (z-Achse)
    start: Vec3 = (0.0, 0.0, 0.0)
    ende: Vec3 = (8.0, 0.0, 0.0)
    orientierung: Vec3 = (0.0, 0.0, 1.0)

    ts = Traversenstrecke(
        traverse_name_intern="prolyte_h30v",
        start=start,
        ende=ende,
        orientierung=orientierung,
    )

    # Windkraft berechnen
    k = ts.windkraft()

    # Ergebnis per print ausgeben (wie console.log)
    print("=== WINDKRAFT ===")
    print("Einzelkräfte:", k.Einzelkraefte)
    print("Resultierende:", k.Resultierende)
    print("Angriffslinie:", k.Angriffsflaeche_Einzelkraefte)

if __name__ == "__main__":
    main()