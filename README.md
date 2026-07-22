# Budzet Domowy

Desktopowa aplikacja (PyQt6) do domowego budzetowania - planowanie i sledzenie
przychodow/wydatkow miesiac po miesiacu, ze wsparciem dla podsumowan rocznych.
Stylistyka inspirowana Windows Fluent Design.

## Funkcje

- **Widok miesiaca** - przelaczanie strzalkami lub z listy rozwijanej; dwie
  karty obok siebie: **Planowane** i **Faktyczne**, kazda z przychodami
  i wydatkami w jednej siatce (kolumna z kwotami zawsze w tym samym miejscu).
- **Edycja kwot wprost w polu** - reczna zmiana laczej kwoty kategorii dopisuje
  wpis korygujacy do historii, wiec suma i historia pojedynczych wpisow nigdy
  sie nie rozjezdzaja.
- **Pojedyncze wpisy pod kategorie** - przycisk "+" przy kazdej kategorii w
  kolumnie Planowane pozwala dodac konkretny zaplanowany wydatek/przychod
  (np. pod "Zakupy": "buty - 200 zl"). Klikniecie w nazwe kategorii otwiera
  liste jej wpisow (planowanych lub faktycznych) z mozliwoscia dodawania
  i usuwania pojedynczo.
- **Szybkie dodawanie** - przycisk "+ Dodaj" na gornym pasku dodaje faktyczny
  wpis do dowolnej widocznej kategorii.
- **Kategorie globalne** - dodawanie i zmiana nazwy kategorii dotyczy calej
  historii (wazne dla podsumowania rocznego). Kategorie mozna natomiast
  **ukryc tylko dla wybranego miesiaca** (odpowiednik "usuniecia" bez utraty
  danych) - ukrycie jest zablokowane, jesli w danym miesiacu sa juz pod nia
  faktyczne wpisy.
- **Historia** - pelny spis wszystkich wpisow (faktycznych i planowanych)
  z mozliwoscia usuwania.
- **Podsumowanie roczne** - sumy faktyczne po kategoriach za caly rok,
  liczone ze wszystkich miesiecy, nawet jesli kategoria byla w ktoryms z nich
  ukryta.
- **Bilans** - kafelki z bilansem planowanym, faktycznym oraz roznica
  miedzy nimi, plus rozbicie przychodow/wydatkow plan vs fakt.

## Model danych

Dane trzymane sa w pliku `budget_data.json` obok skryptu (w trakcie
developmentu) albo obok pliku `.exe` (po zbudowaniu przez PyInstaller).

```
{
  "categories": {
    "income": ["Wyplata", "Freelance", ...],
    "expense": ["Jedzenie", "Kasyno", ...]
  },
  "months": {
    "2026-07": {
      "hidden": {"income": [], "expense": []},
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
```

Kluczowe zasady:

- **Kategorie sa globalne** - jedna tozsamosc na caly czas, dzieki czemu
  mozna policzyc np. "ile wyszlo na Kasyno w 2026" nawet jesli kategoria
  byla w niektorych miesiacach ukryta.
- **"Usuniecie" kategorii z miesiaca = ukrycie** - kategoria i jej historia
  zostaja w danych, znika tylko z widoku danego miesiaca. Mozna ja ukryc
  tylko wtedy, gdy w tym miesiacu nie ma pod nia zadnych faktycznych wpisow.
- **Budzet planowany to lista pojedynczych wpisow**, a nie jedna laczna
  kwota - suma wpisow = to, co widac jako "budzet" kategorii. Reczna edycja
  laczej kwoty w GUI dopisuje wpis korygujacy (roznice), zeby historia
  zostala spojna.
- Przy tworzeniu nowego miesiaca **wpisy planowane startuja jako kopia
  najblizszego wczesniejszego miesiaca** (nie trzeba wpisywac powtarzajacego
  sie budzetu od nowa), natomiast **widocznosc kategorii (hidden) nigdy nie
  jest dziedziczona** - kazdy miesiac startuje z pelna widocznoscia.

## Struktura projektu

```
requirements.txt        # zaleznosci (PyQt6)
BudzetDomowy.spec        # konfiguracja PyInstaller do budowania .exe
budget_config.py          # logika danych: wczytywanie/zapis, sumy, kategorie
budget_app.py             # GUI (PyQt6) - okno glowne i wszystkie dialogi
```

## Uruchomienie (development)

```bash
pip install -r requirements.txt
python budget_app.py
```

## Budowanie do .exe (Windows, PyInstaller)

```bash
pip install pyinstaller
pyinstaller BudzetDomowy.spec
```

Gotowy plik pojawi sie w `dist/BudzetDomowy.exe`. Plik `budget_data.json`
zostanie utworzony obok .exe przy pierwszym uruchomieniu.

## Wymagania

- Python 3.10+
- PyQt6 >= 6.6
