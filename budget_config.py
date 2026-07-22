"""
Ladowanie i zapisywanie danych budzetu.
Dane trzymaja sie w pliku budget_data.json obok programu (albo obok .exe po zbudowaniu).

MODEL DANYCH:
- Kategorie sa GLOBALNE (jedna tozsamosc na caly czas) - dzieki temu da sie zrobic
  podsumowanie roczne typu "ile wyszlo na kasyno w 2026", nawet jesli kategoria
  byla w niektorych miesiacach ukryta.
- "Usuniecie" kategorii z miesiaca w GUI to w rzeczywistosci ukrycie: kategoria
  i cala jej historia zostaja w danych, znika tylko z widoku TEGO miesiaca.
  Mozna ja ukryc TYLKO jesli w danym miesiacu nie ma pod nia zadnych faktycznych
  wpisow (bo inaczej realny wydatek zniknalby z widoku bez ostrzezenia).
- PLANOWANE budzety to (tak jak faktyczne wydatki) LISTA POJEDYNCZYCH WPISOW pod
  kategorie (np. pod "Zakupy": "buty 200", "prezent 150"), nie jedna laczna kwota.
  Suma wpisow planowanych = to, co widac jako "budzet" kategorii. Reczna edycja
  laczej kwoty w GUI dopisuje wpis korygujacy (roznica), zeby historia zostala spojna.

Struktura danych:
{
    "categories": {"income": ["Wyplata", ...], "expense": ["Jedzenie", "Kasyno", ...]},
    "months": {
        "2026-07": {
            "hidden": {"income": [], "expense": []},          # ukryte w LIPCU
            "planned_entries": [
                {"type": "expense", "category": "Zakupy", "amount": 200.0, "note": "buty"}
            ],
            "actual_entries": [
                {"type": "expense", "category": "Jedzenie", "amount": 40.0,
                 "note": "obiad na miescie", "date": "2026-07-21"}
            ]
        }
    }
}
"""
import json
import sys
from datetime import date
from pathlib import Path

STARTER_CATEGORIES = {
    "income": ["Wyplata", "Freelance"],
    "expense": ["Jedzenie", "Zakupy", "Rachunki", "Rozrywka"],
}


def base_dir() -> Path:
    """Folder obok .exe (po spakowaniu PyInstallerem) albo obok skryptu (w trakcie developmentu)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def data_path() -> Path:
    return base_dir() / "budget_data.json"


def load_data() -> dict:
    path = data_path()
    if not path.exists():
        data = {"categories": {"income": list(STARTER_CATEGORIES["income"]),
                                "expense": list(STARTER_CATEGORIES["expense"])},
                "months": {}}
        save_data(data)
        return data
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        data = {"categories": {"income": [], "expense": []}, "months": {}}
    data.setdefault("categories", {"income": [], "expense": []})
    data["categories"].setdefault("income", [])
    data["categories"].setdefault("expense", [])
    data.setdefault("months", {})
    return data


def save_data(data: dict) -> None:
    with open(data_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def current_month_key() -> str:
    return date.today().strftime("%Y-%m")


def shift_month_key(month_key: str, delta: int) -> str:
    y, m = map(int, month_key.split("-"))
    idx = y * 12 + (m - 1) + delta
    y2, m2 = divmod(idx, 12)
    return f"{y2:04d}-{m2 + 1:02d}"


def _planned_entries_from_nearest_earlier(data: dict, month_key: str) -> list:
    candidates = sorted(k for k in data["months"].keys() if k < month_key)
    if not candidates:
        return []
    prev = data["months"][candidates[-1]]
    # kopia (nie referencja) - kolejne miesiace maja niezalezne wpisy budzetu
    return [dict(e) for e in prev.get("planned_entries", [])]


def ensure_month(data: dict, month_key: str) -> dict:
    """Zwraca dane miesiaca, tworzac go jesli jeszcze nie istnieje.

    Wpisy planowane (budzet) startuja jako kopia najblizszego wczesniejszego
    miesiaca (zeby nie wpisywac powtarzajacego sie budzetu od nowa co miesiac).
    Widocznosc kategorii (hidden) NIGDY nie jest dziedziczona - kazdy miesiac
    startuje z pelna widocznoscia wszystkich kategorii.
    """
    if month_key not in data["months"]:
        data["months"][month_key] = {
            "hidden": {"income": [], "expense": []},
            "planned_entries": _planned_entries_from_nearest_earlier(data, month_key),
            "actual_entries": [],
        }

    month = data["months"][month_key]
    month.setdefault("hidden", {"income": [], "expense": []})
    month["hidden"].setdefault("income", [])
    month["hidden"].setdefault("expense", [])
    month.setdefault("planned_entries", [])
    month.setdefault("actual_entries", [])
    return month


def visible_categories(data: dict, month: dict, typ: str) -> list:
    hidden = set(month["hidden"][typ])
    return [c for c in data["categories"][typ] if c not in hidden]


def _sums_from_entries(entries: list) -> dict:
    sums = {"income": {}, "expense": {}}
    for entry in entries:
        typ = entry["type"]
        cat = entry["category"]
        sums[typ][cat] = sums[typ].get(cat, 0.0) + entry["amount"]
    return sums


def actual_sums(month: dict) -> dict:
    """Sumy PO KATEGORIACH dla danego miesiaca - liczone ze wszystkich wpisow,
    niezaleznie od tego czy kategoria jest w tym miesiacu ukryta (pieniadze
    realnie wydane licza sie do bilansu nawet jesli wiersz jest schowany)."""
    return _sums_from_entries(month["actual_entries"])


def planned_sums(month: dict) -> dict:
    """Sumy planowanego budzetu po kategoriach - z pojedynczych wpisow planned_entries."""
    return _sums_from_entries(month["planned_entries"])


def add_entry(data: dict, month_key: str, typ: str, category: str, amount: float, note: str = "") -> None:
    month = ensure_month(data, month_key)
    month["actual_entries"].append({
        "type": typ,
        "category": category,
        "amount": amount,
        "note": note,
        "date": date.today().isoformat(),
    })
    save_data(data)


def delete_entry(data: dict, month_key: str, index: int) -> None:
    month = data["months"][month_key]
    if 0 <= index < len(month["actual_entries"]):
        del month["actual_entries"][index]
        save_data(data)


def add_planned_entry(data: dict, month_key: str, typ: str, category: str, amount: float, note: str = "") -> None:
    """Dodaje pojedynczy zaplanowany wydatek/przychod pod kategorie (np. 'buty' - 200 zl
    pod 'Zakupy'), zamiast nadpisywac laczna kwote budzetu kategorii."""
    month = ensure_month(data, month_key)
    month["planned_entries"].append({
        "type": typ,
        "category": category,
        "amount": amount,
        "note": note,
    })
    save_data(data)


def delete_planned_entry(data: dict, month_key: str, index: int) -> None:
    month = data["months"][month_key]
    if 0 <= index < len(month["planned_entries"]):
        del month["planned_entries"][index]
        save_data(data)


def set_planned_total(data: dict, month_key: str, typ: str, category: str, new_total: float) -> None:
    """Reczna edycja LACZNEJ kwoty budzetu kategorii w GUI: dopisuje wpis korygujacy
    (roznica miedzy nowa a obecna suma), zeby historia pojedynczych wpisow zostala spojna."""
    month = ensure_month(data, month_key)
    current = planned_sums(month)[typ].get(category, 0.0)
    delta = new_total - current
    if delta != 0:
        month["planned_entries"].append({
            "type": typ,
            "category": category,
            "amount": delta,
            "note": "korekta reczna",
        })
    save_data(data)


def set_actual_total(data: dict, month_key: str, typ: str, category: str, new_total: float) -> None:
    """Reczna edycja LACZNEJ kwoty faktycznej kategorii - jak wyzej, ale dla actual_entries."""
    month = ensure_month(data, month_key)
    current = actual_sums(month)[typ].get(category, 0.0)
    delta = new_total - current
    if delta != 0:
        month["actual_entries"].append({
            "type": typ,
            "category": category,
            "amount": delta,
            "note": "korekta reczna",
            "date": date.today().isoformat(),
        })
    save_data(data)


def add_category(data: dict, typ: str, name: str) -> None:
    """Dodaje kategorie GLOBALNIE (widoczna od tej pory we wszystkich miesiacach)."""
    name = name.strip()
    if not name or name in data["categories"][typ]:
        return
    data["categories"][typ].append(name)
    save_data(data)


def rename_category(data: dict, typ: str, old_name: str, new_name: str) -> None:
    """Zmienia nazwe kategorii GLOBALNIE - we wszystkich miesiacach, planach i wpisach."""
    new_name = new_name.strip()
    if not new_name or old_name not in data["categories"][typ] or new_name in data["categories"][typ]:
        return
    idx = data["categories"][typ].index(old_name)
    data["categories"][typ][idx] = new_name
    for month in data["months"].values():
        if old_name in month["hidden"].get(typ, []):
            month["hidden"][typ] = [new_name if c == old_name else c for c in month["hidden"][typ]]
        for entry in month["actual_entries"]:
            if entry["type"] == typ and entry["category"] == old_name:
                entry["category"] = new_name
        for entry in month.get("planned_entries", []):
            if entry["type"] == typ and entry["category"] == old_name:
                entry["category"] = new_name
    save_data(data)


def can_hide_category(data: dict, month_key: str, typ: str, name: str) -> bool:
    """False, jesli w tym miesiacu jest juz jakikolwiek faktyczny wpis pod ta kategoria."""
    month = ensure_month(data, month_key)
    sums = actual_sums(month)
    return sums[typ].get(name, 0.0) == 0.0


def hide_category(data: dict, month_key: str, typ: str, name: str) -> bool:
    """Ukrywa kategorie TYLKO w danym miesiacu. Zwraca False (i nic nie robi),
    jesli w tym miesiacu sa juz pod nia faktyczne wpisy - patrz can_hide_category()."""
    if not can_hide_category(data, month_key, typ, name):
        return False
    month = ensure_month(data, month_key)
    if name not in month["hidden"][typ]:
        month["hidden"][typ].append(name)
    save_data(data)
    return True


def show_category(data: dict, month_key: str, typ: str, name: str) -> None:
    """Przywraca widocznosc kategorii w danym miesiacu."""
    month = ensure_month(data, month_key)
    if name in month["hidden"][typ]:
        month["hidden"][typ].remove(name)
    save_data(data)


def annual_totals(data: dict, year: int) -> dict:
    """Sumy faktyczne PO KATEGORIACH za caly rok (wszystkie miesiace, wliczajac te,
    w ktorych kategoria byla akurat ukryta - historia sie nie traci)."""
    totals = {"income": {}, "expense": {}}
    for month_key, month in data["months"].items():
        if not month_key.startswith(f"{year:04d}-"):
            continue
        sums = actual_sums(month)
        for typ in ("income", "expense"):
            for cat, val in sums[typ].items():
                totals[typ][cat] = totals[typ].get(cat, 0.0) + val
    return totals
