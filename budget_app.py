"""
Budzet domowy - GUI (PyQt6, stylistyka inspirowana Windows Fluent Design)

Okno glowne:
- wybor miesiaca (strzalki + lista rozwijana)
- dwie karty obok siebie: PLANOWANE i FAKTYCZNE, kazda z przychodami i wydatkami
  ulozonymi w jednej siatce (QGridLayout) na cala karte - dzieki temu kolumna
  z kwotami jest dokladnie w tym samym miejscu we wszystkich wierszach.
- kwoty w obu kolumnach sa edytowalne wprost w polu; reczna edycja dopisuje
  wpis korygujacy do historii (zeby suma i historia nigdy sie nie rozjechaly)
- przy kazdym wierszu w kolumnie PLANOWANE jest male "+" do dodania pojedynczego
  zaplanowanego wydatku/przychodu pod ta konkretna kategorie (np. pod "Zakupy":
  "buty - 200 zl")
- "+ Dodaj" (gorny pasek) - szybkie dodawanie FAKTYCZNEGO wpisu do dowolnej kategorii
- kategorie sa GLOBALNE (dodawanie/zmiana nazwy dotyczy calej historii), ale
  widocznosc mozna wylaczyc dla POJEDYNCZEGO miesiaca - patrz "Kategorie"
- "Podsumowanie roczne" - sumy po kategoriach za caly rok
- "Historia" - wszystkie wpisy (faktyczne i planowane) z mozliwoscia usuwania
"""
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFormLayout, QFrame, QLabel, QLineEdit, QComboBox, QPushButton, QRadioButton, QButtonGroup,
    QListWidget, QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget, QHeaderView,
    QAbstractItemView, QGraphicsDropShadowEffect, QSizePolicy,
)

import budget_config as cfgmod

# --- Paleta kolorow: neutralne fluent-owe tla + akcent marki (Twitch Reward Alerts) ---
WINDOW_BG = "#1e1e1e"
CARD_BG = "#292929"
CARD_BORDER = "rgba(255, 255, 255, 0.07)"
FIELD_BG = "rgba(255, 255, 255, 0.05)"
FIELD_BORDER = "rgba(255, 255, 255, 0.12)"
SUBTLE_BG = "rgba(255, 255, 255, 0.06)"
SUBTLE_HOVER = "rgba(255, 255, 255, 0.11)"
DIVIDER = "rgba(255, 255, 255, 0.08)"

ACCENT = "#843935"
ACCENT_HOVER = "#9c453f"
ACCENT_GLOW = "#ff6a52"

FG_TEXT = "#f2f2f2"
FG_MUTED = "#9a9a9a"
GREEN = "#5fd97a"
RED = "#e05a4f"

MONTH_NAMES = ["Styczen", "Luty", "Marzec", "Kwiecien", "Maj", "Czerwiec",
               "Lipiec", "Sierpien", "Wrzesien", "Pazdziernik", "Listopad", "Grudzien"]

FLUENT_FONT = "'Segoe UI Variable Text', 'Segoe UI', sans-serif"

STYLESHEET = f"""
QWidget {{
    background-color: {WINDOW_BG};
    color: {FG_TEXT};
    font-family: {FLUENT_FONT};
    font-size: 10pt;
}}
QMainWindow, QDialog {{
    background-color: {WINDOW_BG};
}}
QFrame#Card {{
    background-color: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 10px;
}}
QLabel#SectionHeader {{
    color: {FG_TEXT};
    font-weight: 600;
    font-size: 10.5pt;
    padding: 2px 0 4px 0;
}}
QLabel#CardTitle {{
    color: {FG_TEXT};
    font-weight: 700;
    font-size: 12pt;
}}
QLabel#Muted {{
    color: {FG_MUTED};
}}
QLineEdit, QComboBox {{
    background-color: {FIELD_BG};
    border: 1px solid {FIELD_BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    color: {FG_TEXT};
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {ACCENT_GLOW};
}}
QLineEdit:hover, QComboBox:hover {{
    border: 1px solid rgba(255, 255, 255, 0.22);
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    selection-background-color: {ACCENT};
    border: 1px solid {CARD_BORDER};
    outline: none;
    border-radius: 6px;
}}
QPushButton#AccentButton {{
    background-color: {ACCENT};
    color: {FG_TEXT};
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 600;
}}
QPushButton#AccentButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#AccentButton:pressed {{
    background-color: #6e2e2a;
}}
QPushButton#SubtleButton {{
    background-color: {SUBTLE_BG};
    color: {FG_TEXT};
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
}}
QPushButton#SubtleButton:hover {{
    background-color: {SUBTLE_HOVER};
}}
QPushButton#IconButton {{
    background-color: {SUBTLE_BG};
    color: {FG_TEXT};
    border: none;
    border-radius: 6px;
    font-weight: 700;
}}
QPushButton#IconButton:hover {{
    background-color: {ACCENT};
}}
QListWidget, QTableWidget {{
    background-color: {FIELD_BG};
    border: 1px solid {FIELD_BORDER};
    border-radius: 8px;
    gridline-color: {DIVIDER};
}}
QListWidget::item, QTableWidget::item {{
    padding: 5px;
}}
QListWidget::item:selected, QTableWidget::item:selected {{
    background-color: {ACCENT};
    color: {FG_TEXT};
}}
QHeaderView::section {{
    background-color: transparent;
    color: {FG_MUTED};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {DIVIDER};
}}
QTabWidget::pane {{
    border: 1px solid {CARD_BORDER};
    border-radius: 8px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {FG_MUTED};
    padding: 8px 18px;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {FG_TEXT};
    border-bottom: 2px solid {ACCENT_GLOW};
}}
QRadioButton::indicator {{
    width: 15px;
    height: 15px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {SUBTLE_BG};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {SUBTLE_HOVER};
}}
QFrame#StatTile {{
    background-color: {SUBTLE_BG};
    border-radius: 8px;
}}
QLabel#StatValue {{
    font-size: 17pt;
    font-weight: 700;
}}
"""


def fmt_month(month_key: str) -> str:
    y, m = month_key.split("-")
    return f"{MONTH_NAMES[int(m) - 1]} {y}"


def fmt_amount(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def parse_amount(text: str):
    try:
        return float(text.replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def accent_button(text):
    btn = QPushButton(text)
    btn.setObjectName("AccentButton")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def subtle_button(text):
    btn = QPushButton(text)
    btn.setObjectName("SubtleButton")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def icon_button(text, size=26):
    btn = QPushButton(text)
    btn.setObjectName("IconButton")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedSize(size, size)
    return btn


def make_card(title: str) -> tuple:
    """Zwraca (frame, content_layout) - karta z fluent-owym cieniem i naglowkiem."""
    frame = QFrame()
    frame.setObjectName("Card")
    shadow = QGraphicsDropShadowEffect(frame)
    shadow.setBlurRadius(28)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(0, 0, 0, 110))
    frame.setGraphicsEffect(shadow)

    outer = QVBoxLayout(frame)
    outer.setContentsMargins(18, 16, 18, 16)
    outer.setSpacing(10)
    if title:
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        outer.addWidget(title_label)
    return frame, outer


def make_stat_tile(label_text: str):
    """Kafelek statystyki: maly naglowek + duza wartosc. Zwraca (frame, value_label) -
    value_label mozna potem podmieniac tekst/kolor."""
    frame = QFrame()
    frame.setObjectName("StatTile")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(4)

    label = QLabel(label_text)
    label.setObjectName("Muted")
    layout.addWidget(label)

    value_label = QLabel("0,00 zl")
    value_label.setObjectName("StatValue")
    layout.addWidget(value_label)

    return frame, value_label


class AmountGrid:
    """Wspolna siatka kwot dla sekcji kategorii - gwarantuje, ze kolumna z kwota
    (i ewentualny 'diff'/'+') jest w tym samym miejscu w kazdym wierszu."""

    NAME_COL = 0
    VALUE_COL = 1
    EXTRA_COL = 2

    def __init__(self, extra_col=False):
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(4)
        self.grid.setColumnStretch(self.NAME_COL, 1)
        self.grid.setColumnMinimumWidth(self.VALUE_COL, 100)
        if extra_col:
            self.grid.setColumnMinimumWidth(self.EXTRA_COL, 96)
        self.row = 0

    def add_header(self, text):
        label = QLabel(text)
        label.setObjectName("SectionHeader")
        self.grid.addWidget(label, self.row, self.NAME_COL, 1, 3)
        self.row += 1

    def add_empty(self, text):
        label = QLabel(text)
        label.setObjectName("Muted")
        self.grid.addWidget(label, self.row, self.NAME_COL, 1, 3)
        self.row += 1

    def add_row(self, name_widget, value_widget, extra_widget=None):
        self.grid.addWidget(name_widget, self.row, self.NAME_COL)
        self.grid.addWidget(value_widget, self.row, self.VALUE_COL)
        if extra_widget is not None:
            self.grid.addWidget(extra_widget, self.row, self.EXTRA_COL)
        self.row += 1

    def clear(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.row = 0


class QuickAddDialog(QDialog):
    """Szybkie dodawanie FAKTYCZNEGO wpisu do dowolnej (widocznej) kategorii."""

    def __init__(self, parent, categories):
        super().__init__(parent)
        self.setWindowTitle("Szybkie dodawanie")
        self.categories = categories
        self.result_data = None

        layout = QVBoxLayout(self)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Typ:"))
        self.expense_radio = QRadioButton("Wydatek")
        self.income_radio = QRadioButton("Przychod")
        self.expense_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.expense_radio)
        group.addButton(self.income_radio)
        type_row.addWidget(self.expense_radio)
        type_row.addWidget(self.income_radio)
        type_row.addStretch()
        layout.addLayout(type_row)

        form = QFormLayout()
        self.category_combo = QComboBox()
        form.addRow("Kategoria:", self.category_combo)
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("np. 59,90")
        form.addRow("Kwota:", self.amount_edit)
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("opcjonalnie")
        form.addRow("Notatka:", self.note_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        add_btn = accent_button("Dodaj")
        cancel_btn = subtle_button("Anuluj")
        add_btn.clicked.connect(self._submit)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.expense_radio.toggled.connect(self._refresh_categories)
        self._refresh_categories()
        self.amount_edit.setFocus()

    def _refresh_categories(self):
        typ = "expense" if self.expense_radio.isChecked() else "income"
        self.category_combo.clear()
        self.category_combo.addItems(self.categories.get(typ, []))

    def _submit(self):
        typ = "expense" if self.expense_radio.isChecked() else "income"
        category = self.category_combo.currentText()
        if not category:
            QMessageBox.critical(self, "Brak kategorii",
                                 "Ten miesiac nie ma jeszcze zadnej widocznej kategorii tego typu.")
            return
        amount = parse_amount(self.amount_edit.text())
        if amount is None:
            QMessageBox.critical(self, "Zla kwota", "Podaj poprawna kwote, np. 59.90")
            return
        if amount <= 0:
            QMessageBox.critical(self, "Zla kwota", "Kwota musi byc wieksza od zera.")
            return
        self.result_data = (typ, category, amount, self.note_edit.text().strip())
        self.accept()


class AddPlannedItemDialog(QDialog):
    """Dodanie POJEDYNCZEGO wpisu (planowanego lub faktycznego) pod KONKRETNA kategorie
    - kategoria i typ sa juz ustalone (uzywane przy '+' w kolumnie Planowane oraz
    przy przycisku 'Dodaj' w oknie szczegolow kategorii)."""

    def __init__(self, parent, typ, category, title=None):
        super().__init__(parent)
        self.setWindowTitle(title or f"Dodaj do planu: {category}")
        self.typ = typ
        self.category = category
        self.result_data = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Kategoria:", QLabel(category))
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("np. 200")
        form.addRow("Kwota:", self.amount_edit)
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("np. buty")
        form.addRow("Notatka:", self.note_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        add_btn = accent_button("Dodaj")
        cancel_btn = subtle_button("Anuluj")
        add_btn.clicked.connect(self._submit)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.amount_edit.setFocus()

    def _submit(self):
        amount = parse_amount(self.amount_edit.text())
        if amount is None or amount == 0:
            QMessageBox.critical(self, "Zla kwota", "Podaj poprawna, niezerowa kwote.")
            return
        self.result_data = (self.typ, self.category, amount, self.note_edit.text().strip())
        self.accept()


class CategoryEntriesDialog(QDialog):
    """Spis pojedynczych wpisow (planowanych albo faktycznych) TYLKO dla jednej
    kategorii - otwierane po kliknieciu w jej nazwe w oknie glownym. Mozna tu
    usunac pojedynczy wpis albo dodac kolejny bez wchodzenia do pelnej Historii."""

    def __init__(self, parent, data, month_key, typ, category, kind):
        super().__init__(parent)
        self.data = data
        self.month_key = month_key
        self.typ = typ
        self.category = category
        self.kind = kind  # "planned" albo "actual"
        self.changed = False

        kind_label = "planowane" if kind == "planned" else "faktyczne"
        self.setWindowTitle(f"{category} - wpisy {kind_label} ({fmt_month(month_key)})")
        self.resize(440, 400)

        layout = QVBoxLayout(self)
        columns = ["Kwota", "Notatka", "Data"] if kind == "actual" else ["Kwota", "Notatka"]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = accent_button("Dodaj kolejny")
        delete_btn = subtle_button("Usun zaznaczony")
        add_btn.clicked.connect(self._add_item)
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        close_btn = subtle_button("Zamknij")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._index_map = []  # mapuje wiersz tabeli -> indeks w pelnej liscie wpisow miesiaca
        self._reload()

    def _full_entries(self):
        month = cfgmod.ensure_month(self.data, self.month_key)
        return month["planned_entries"] if self.kind == "planned" else month["actual_entries"]

    def _reload(self):
        entries = self._full_entries()
        self._index_map = [i for i, e in enumerate(entries)
                           if e["type"] == self.typ and e["category"] == self.category]
        self.table.setRowCount(len(self._index_map))
        for row, idx in enumerate(self._index_map):
            entry = entries[idx]
            self.table.setItem(row, 0, QTableWidgetItem(fmt_amount(entry["amount"])))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("note", "")))
            if self.kind == "actual":
                self.table.setItem(row, 2, QTableWidgetItem(entry["date"]))

    def _add_item(self):
        title = f"Dodaj do planu: {self.category}" if self.kind == "planned" else f"Dodaj wpis: {self.category}"
        dialog = AddPlannedItemDialog(self, self.typ, self.category, title=title)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            typ, category, amount, note = dialog.result_data
            if self.kind == "planned":
                cfgmod.add_planned_entry(self.data, self.month_key, typ, category, amount, note)
            else:
                cfgmod.add_entry(self.data, self.month_key, typ, category, amount, note)
            self.changed = True
            self._reload()

    def _delete_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        real_indices = sorted((self._index_map[r] for r in rows), reverse=True)
        for real_idx in real_indices:
            if self.kind == "planned":
                cfgmod.delete_planned_entry(self.data, self.month_key, real_idx)
            else:
                cfgmod.delete_entry(self.data, self.month_key, real_idx)
        self.changed = True
        self._reload()


def category_link_button(name):
    """Nazwa kategorii jako klikalny 'link' - otwiera spis jej pojedynczych wpisow."""
    btn = QPushButton(name)
    btn.setObjectName("SubtleButton")
    btn.setStyleSheet(
        "QPushButton#SubtleButton { background: transparent; text-align: left; padding: 2px 4px; }"
        "QPushButton#SubtleButton:hover { text-decoration: underline; color: " + ACCENT_GLOW + "; }"
    )
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class CategoryManagerDialog(QDialog):
    """Kategorie sa globalne (dodawanie/zmiana nazwy dzialaja na cala historie).
    'Ukryj'/'Pokaz' dotyczy TYLKO wskazanego miesiaca - to jest odpowiednik
    'usuwania', ale bez utraty danych do podsumowania rocznego. Ukrycie jest
    zablokowane, jesli w tym miesiacu sa juz pod ta kategoria faktyczne wpisy."""

    def __init__(self, parent, data, month_key):
        super().__init__(parent)
        self.setWindowTitle(f"Kategorie - {fmt_month(month_key)}")
        self.resize(480, 480)
        self.data = data
        self.month_key = month_key
        self.changed = False

        layout = QVBoxLayout(self)
        note = QLabel(
            "Dodawanie i zmiana nazwy dotycza calej historii (dla podsumowania rocznego).\n"
            f"Ukrywanie/przywracanie dotyczy tylko miesiaca: {fmt_month(month_key)}."
        )
        note.setObjectName("Muted")
        layout.addWidget(note)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        self.visible_lists = {}
        self.hidden_lists = {}
        for typ, label in (("income", "Przychody"), ("expense", "Wydatki")):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            tab_layout.addWidget(QLabel("Widoczne w tym miesiacu:"))
            visible_list = QListWidget()
            tab_layout.addWidget(visible_list)

            tab_layout.addWidget(QLabel("Ukryte w tym miesiacu:"))
            hidden_list = QListWidget()
            hidden_list.setMaximumHeight(90)
            tab_layout.addWidget(hidden_list)

            move_row = QHBoxLayout()
            hide_btn = subtle_button("Ukryj \u25bc")
            show_btn = subtle_button("Pokaz \u25b2")
            move_row.addWidget(hide_btn)
            move_row.addWidget(show_btn)
            move_row.addStretch()
            tab_layout.addLayout(move_row)

            add_row = QHBoxLayout()
            name_edit = QLineEdit()
            name_edit.setPlaceholderText("nowa kategoria")
            add_row.addWidget(name_edit)
            add_btn = accent_button("Dodaj")
            rename_btn = subtle_button("Zmien nazwe")
            add_row.addWidget(add_btn)
            add_row.addWidget(rename_btn)
            tab_layout.addLayout(add_row)

            hide_btn.clicked.connect(lambda _=False, t=typ, lw=visible_list: self._hide(t, lw))
            show_btn.clicked.connect(lambda _=False, t=typ, lw=hidden_list: self._show(t, lw))
            add_btn.clicked.connect(lambda _=False, t=typ, e=name_edit: self._add(t, e))
            rename_btn.clicked.connect(
                lambda _=False, t=typ, e=name_edit, vlw=visible_list, hlw=hidden_list: self._rename(t, e, vlw, hlw)
            )

            tabs.addTab(tab, label)
            self.visible_lists[typ] = visible_list
            self.hidden_lists[typ] = hidden_list

        close_btn = subtle_button("Zamknij")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._reload_all()

    def _reload_all(self):
        month = cfgmod.ensure_month(self.data, self.month_key)
        for typ in ("income", "expense"):
            hidden = set(month["hidden"][typ])
            self.visible_lists[typ].clear()
            self.visible_lists[typ].addItems([c for c in self.data["categories"][typ] if c not in hidden])
            self.hidden_lists[typ].clear()
            self.hidden_lists[typ].addItems([c for c in self.data["categories"][typ] if c in hidden])

    def _add(self, typ, name_edit):
        name = name_edit.text().strip()
        if not name:
            return
        cfgmod.add_category(self.data, typ, name)
        name_edit.clear()
        self._reload_all()
        self.changed = True

    def _rename(self, typ, name_edit, visible_list, hidden_list):
        item = visible_list.currentItem() or hidden_list.currentItem()
        new_name = name_edit.text().strip()
        if item is None or not new_name:
            QMessageBox.information(self, "Zmiana nazwy",
                                    "Zaznacz kategorie na jednej z list i wpisz nowa nazwe w polu.")
            return
        cfgmod.rename_category(self.data, typ, item.text(), new_name)
        name_edit.clear()
        self._reload_all()
        self.changed = True

    def _hide(self, typ, visible_list):
        item = visible_list.currentItem()
        if item is None:
            return
        name = item.text()
        if not cfgmod.can_hide_category(self.data, self.month_key, typ, name):
            QMessageBox.warning(
                self, "Nie mozna ukryc",
                f"W tym miesiacu sa juz wpisy pod '{name}' - ukrycie schowaloby realny wydatek/przychod bez ostrzezenia.\n"
                "Usun najpierw te wpisy w 'Historia', albo zostaw kategorie widoczna."
            )
            return
        cfgmod.hide_category(self.data, self.month_key, typ, name)
        self._reload_all()
        self.changed = True

    def _show(self, typ, hidden_list):
        item = hidden_list.currentItem()
        if item is None:
            return
        cfgmod.show_category(self.data, self.month_key, typ, item.text())
        self._reload_all()
        self.changed = True


class HistoryDialog(QDialog):
    """Historia wpisow - zakladka Faktyczne i zakladka Planowane, kazda z usuwaniem."""

    def __init__(self, parent, data, month_key):
        super().__init__(parent)
        self.setWindowTitle(f"Historia - {fmt_month(month_key)}")
        self.resize(580, 460)
        self.data = data
        self.month_key = month_key
        self.changed = False

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        self.actual_table = QTableWidget(0, 5)
        self.actual_table.setHorizontalHeaderLabels(["Typ", "Kategoria", "Kwota", "Notatka", "Data"])
        self._prep_table(self.actual_table, stretch_cols=(1, 3))
        actual_tab = QWidget()
        actual_layout = QVBoxLayout(actual_tab)
        actual_layout.addWidget(self.actual_table)
        actual_delete = accent_button("Usun zaznaczony wpis")
        actual_delete.clicked.connect(self._delete_actual)
        actual_layout.addWidget(actual_delete)
        tabs.addTab(actual_tab, "Faktyczne")

        self.planned_table = QTableWidget(0, 4)
        self.planned_table.setHorizontalHeaderLabels(["Typ", "Kategoria", "Kwota", "Notatka"])
        self._prep_table(self.planned_table, stretch_cols=(1, 3))
        planned_tab = QWidget()
        planned_layout = QVBoxLayout(planned_tab)
        planned_layout.addWidget(self.planned_table)
        planned_delete = accent_button("Usun zaznaczony wpis")
        planned_delete.clicked.connect(self._delete_planned)
        planned_layout.addWidget(planned_delete)
        tabs.addTab(planned_tab, "Planowane")

        self._reload()

    def _prep_table(self, table, stretch_cols=()):
        for col in stretch_cols:
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def _reload(self):
        month = cfgmod.ensure_month(self.data, self.month_key)

        entries = month["actual_entries"]
        self.actual_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            typ_label = "Przychod" if entry["type"] == "income" else "Wydatek"
            values = [typ_label, entry["category"], fmt_amount(entry["amount"]), entry.get("note", ""), entry["date"]]
            for col, val in enumerate(values):
                self.actual_table.setItem(row, col, QTableWidgetItem(val))

        planned = month["planned_entries"]
        self.planned_table.setRowCount(len(planned))
        for row, entry in enumerate(planned):
            typ_label = "Przychod" if entry["type"] == "income" else "Wydatek"
            values = [typ_label, entry["category"], fmt_amount(entry["amount"]), entry.get("note", "")]
            for col, val in enumerate(values):
                self.planned_table.setItem(row, col, QTableWidgetItem(val))

    def _delete_actual(self):
        rows = sorted({idx.row() for idx in self.actual_table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for row in rows:
            cfgmod.delete_entry(self.data, self.month_key, row)
        self.changed = True
        self._reload()

    def _delete_planned(self):
        rows = sorted({idx.row() for idx in self.planned_table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for row in rows:
            cfgmod.delete_planned_entry(self.data, self.month_key, row)
        self.changed = True
        self._reload()


class AnnualSummaryDialog(QDialog):
    """Podsumowanie roczne po kategoriach - liczy WSZYSTKIE faktyczne wpisy w danym
    roku, niezaleznie od tego, czy kategoria byla w ktoryms miesiacu ukryta."""

    def __init__(self, parent, data, year):
        super().__init__(parent)
        self.setWindowTitle(f"Podsumowanie roczne - {year}")
        self.resize(460, 480)

        totals = cfgmod.annual_totals(data, year)
        layout = QVBoxLayout(self)

        for typ, label in (("income", "Przychody"), ("expense", "Wydatki")):
            card, card_layout = make_card(label)
            items = sorted(totals[typ].items(), key=lambda kv: kv[1], reverse=True)
            if not items:
                empty = QLabel("(brak wpisow w tym roku)")
                empty.setObjectName("Muted")
                card_layout.addWidget(empty)
            for cat, total in items:
                row = QHBoxLayout()
                name_label = QLabel(cat)
                name_label.setFixedWidth(180)
                value_label = QLabel(f"{fmt_amount(total)} zl")
                value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                row.addWidget(name_label)
                row.addWidget(value_label)
                card_layout.addLayout(row)
            layout.addWidget(card)

        close_btn = subtle_button("Zamknij")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budzet domowy")
        self.resize(1020, 700)

        self.data = cfgmod.load_data()
        self.month_key = cfgmod.current_month_key()
        cfgmod.ensure_month(self.data, self.month_key)
        self._month_key_by_label = {}

        self._build_ui()
        self._refresh_all()

    # ---------------------------------------------------------------- UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(8)
        prev_btn = icon_button("\u25c0")
        next_btn = icon_button("\u25b6")
        prev_btn.clicked.connect(self._prev_month)
        next_btn.clicked.connect(self._next_month)
        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(170)
        self.month_combo.currentIndexChanged.connect(self._on_month_selected)

        top.addWidget(prev_btn)
        top.addWidget(self.month_combo)
        top.addWidget(next_btn)
        top.addSpacing(20)

        add_btn = accent_button("+  Dodaj")
        add_btn.clicked.connect(self._open_quick_add)
        top.addWidget(add_btn)

        history_btn = subtle_button("Historia")
        history_btn.clicked.connect(self._open_history)
        top.addWidget(history_btn)

        top.addStretch()

        annual_btn = subtle_button("Podsumowanie roczne")
        annual_btn.clicked.connect(self._open_annual_summary)
        top.addWidget(annual_btn)

        categories_btn = subtle_button("Kategorie")
        categories_btn.clicked.connect(self._open_category_manager)
        top.addWidget(categories_btn)

        root.addLayout(top)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        self.planned_card, self.planned_card_layout = make_card("Planowane")
        self.actual_card, self.actual_card_layout = make_card("Faktyczne")
        columns.addWidget(self.planned_card, 1)
        columns.addWidget(self.actual_card, 1)
        root.addLayout(columns, 1)

        self.planned_grid = AmountGrid(extra_col=True)
        self.planned_card_layout.addLayout(self.planned_grid.grid)
        self.planned_card_layout.addStretch()

        self.actual_grid = AmountGrid(extra_col=True)
        self.actual_card_layout.addLayout(self.actual_grid.grid)
        self.actual_card_layout.addStretch()

        summary_card, summary_layout = make_card("Bilans")

        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(12)
        self.planned_tile, self.planned_value_label = make_stat_tile("Bilans planowany")
        self.actual_tile, self.actual_value_label = make_stat_tile("Bilans faktyczny")
        self.diff_tile, self.diff_value_label = make_stat_tile("Roznica od planu")
        tiles_row.addWidget(self.planned_tile)
        tiles_row.addWidget(self.actual_tile)
        tiles_row.addWidget(self.diff_tile)
        summary_layout.addLayout(tiles_row)

        self.breakdown_label = QLabel("")
        self.breakdown_label.setObjectName("Muted")
        summary_layout.addWidget(self.breakdown_label)

        root.addWidget(summary_card)

    # ----------------------------------------------------------- odswiezanie

    def _refresh_all(self):
        month_keys = sorted(set(self.data["months"].keys()) | {self.month_key})
        self._month_key_by_label = {fmt_month(k): k for k in month_keys}
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        self.month_combo.addItems([fmt_month(k) for k in month_keys])
        self.month_combo.setCurrentText(fmt_month(self.month_key))
        self.month_combo.blockSignals(False)

        month = cfgmod.ensure_month(self.data, self.month_key)
        actual = cfgmod.actual_sums(month)
        planned = cfgmod.planned_sums(month)

        self.planned_grid.clear()
        self._render_planned_section(self.planned_grid, "income", "Przychody", month, planned)
        self._render_planned_section(self.planned_grid, "expense", "Wydatki", month, planned)

        self.actual_grid.clear()
        self._render_actual_section(self.actual_grid, "income", "Przychody", month, actual, planned)
        self._render_actual_section(self.actual_grid, "expense", "Wydatki", month, actual, planned)

        total_planned_income = sum(planned["income"].values())
        total_planned_expense = sum(planned["expense"].values())
        total_actual_income = sum(actual["income"].values())
        total_actual_expense = sum(actual["expense"].values())
        planned_balance = total_planned_income - total_planned_expense
        actual_balance = total_actual_income - total_actual_expense
        diff_from_plan = actual_balance - planned_balance

        self.planned_value_label.setText(f"{fmt_amount(planned_balance)} zl")

        actual_color = GREEN if actual_balance >= 0 else RED
        actual_sign = "+" if actual_balance >= 0 else ""
        self.actual_value_label.setText(f"{actual_sign}{fmt_amount(actual_balance)} zl")
        self.actual_value_label.setStyleSheet(f"color: {actual_color};")

        diff_color = GREEN if diff_from_plan >= 0 else RED
        diff_sign = "+" if diff_from_plan >= 0 else ""
        self.diff_value_label.setText(f"{diff_sign}{fmt_amount(diff_from_plan)} zl")
        self.diff_value_label.setStyleSheet(f"color: {diff_color};")

        self.breakdown_label.setText(
            f"Przychody: plan {fmt_amount(total_planned_income)} / fakt {fmt_amount(total_actual_income)} zl"
            f"    \u2022    "
            f"Wydatki: plan {fmt_amount(total_planned_expense)} / fakt {fmt_amount(total_actual_expense)} zl"
        )

    def _render_planned_section(self, grid, typ, label, month, planned):
        categories = cfgmod.visible_categories(self.data, month, typ)
        grid.add_header(label)
        if not categories:
            grid.add_empty("(brak widocznych kategorii)")
            return
        for cat in categories:
            name_btn = category_link_button(cat)
            name_btn.clicked.connect(lambda _=False, t=typ, c=cat: self._open_category_entries(t, c, "planned"))
            value_edit = QLineEdit(fmt_amount(planned[typ].get(cat, 0.0)))
            value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_edit.editingFinished.connect(
                lambda t=typ, c=cat, e=value_edit: self._save_planned_total(t, c, e)
            )
            plus_btn = icon_button("+", size=26)
            plus_btn.clicked.connect(lambda _=False, t=typ, c=cat: self._open_add_planned_item(t, c))
            grid.add_row(name_btn, value_edit, plus_btn)

    def _render_actual_section(self, grid, typ, label, month, actual, planned):
        categories = cfgmod.visible_categories(self.data, month, typ)
        grid.add_header(label)
        if not categories:
            grid.add_empty("(brak widocznych kategorii)")
            return
        for cat in categories:
            actual_val = actual[typ].get(cat, 0.0)
            planned_val = planned[typ].get(cat, 0.0)
            diff = actual_val - planned_val
            over_budget = (typ == "expense" and actual_val > planned_val) or (typ == "income" and actual_val < planned_val)
            color = RED if over_budget else GREEN

            name_btn = category_link_button(cat)
            name_btn.clicked.connect(lambda _=False, t=typ, c=cat: self._open_category_entries(t, c, "actual"))
            value_edit = QLineEdit(fmt_amount(actual_val))
            value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_edit.editingFinished.connect(
                lambda t=typ, c=cat, e=value_edit: self._save_actual_total(t, c, e)
            )
            sign = "+" if diff >= 0 else ""
            diff_label = QLabel(f"({sign}{fmt_amount(diff)})")
            diff_label.setStyleSheet(f"color: {color};")
            diff_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.add_row(name_btn, value_edit, diff_label)

    def _save_planned_total(self, typ, category, line_edit):
        amount = parse_amount(line_edit.text())
        if amount is None:
            QMessageBox.critical(self, "Zla kwota", f"Niepoprawna kwota dla '{category}'.")
            self._refresh_all()
            return
        cfgmod.set_planned_total(self.data, self.month_key, typ, category, amount)
        self._refresh_all()

    def _save_actual_total(self, typ, category, line_edit):
        amount = parse_amount(line_edit.text())
        if amount is None:
            QMessageBox.critical(self, "Zla kwota", f"Niepoprawna kwota dla '{category}'.")
            self._refresh_all()
            return
        cfgmod.set_actual_total(self.data, self.month_key, typ, category, amount)
        self._refresh_all()

    # -------------------------------------------------------------- akcje

    def _on_month_selected(self, _index):
        label = self.month_combo.currentText()
        self.month_key = self._month_key_by_label.get(label, self.month_key)
        cfgmod.ensure_month(self.data, self.month_key)
        self._refresh_all()

    def _prev_month(self):
        self.month_key = cfgmod.shift_month_key(self.month_key, -1)
        cfgmod.ensure_month(self.data, self.month_key)
        cfgmod.save_data(self.data)
        self._refresh_all()

    def _next_month(self):
        self.month_key = cfgmod.shift_month_key(self.month_key, 1)
        cfgmod.ensure_month(self.data, self.month_key)
        cfgmod.save_data(self.data)
        self._refresh_all()

    def _open_quick_add(self):
        month = cfgmod.ensure_month(self.data, self.month_key)
        categories = {
            "income": cfgmod.visible_categories(self.data, month, "income"),
            "expense": cfgmod.visible_categories(self.data, month, "expense"),
        }
        dialog = QuickAddDialog(self, categories)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            typ, category, amount, note = dialog.result_data
            cfgmod.add_entry(self.data, self.month_key, typ, category, amount, note)
            self._refresh_all()

    def _open_add_planned_item(self, typ, category):
        dialog = AddPlannedItemDialog(self, typ, category)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            typ, category, amount, note = dialog.result_data
            cfgmod.add_planned_entry(self.data, self.month_key, typ, category, amount, note)
            self._refresh_all()

    def _open_category_entries(self, typ, category, kind):
        dialog = CategoryEntriesDialog(self, self.data, self.month_key, typ, category, kind)
        dialog.exec()
        if dialog.changed:
            self._refresh_all()

    def _open_category_manager(self):
        dialog = CategoryManagerDialog(self, self.data, self.month_key)
        dialog.exec()
        if dialog.changed:
            self._refresh_all()

    def _open_history(self):
        dialog = HistoryDialog(self, self.data, self.month_key)
        dialog.exec()
        if dialog.changed:
            self._refresh_all()

    def _open_annual_summary(self):
        year = int(self.month_key.split("-")[0])
        dialog = AnnualSummaryDialog(self, self.data, year)
        dialog.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
