"""Main application window."""

import tkinter as tk
from tkinter import ttk

from gui.dfa_tab import DFATab
from gui.nfa_tab import NFATab
from gui.pda_tab import PDATab
from gui.regex_tab import RegexTab
from gui.cfg_tab import CFGTab
from gui.tm_tab import TMTab


class App(tk.Tk):
    """Main application window with tabbed interface."""

    def __init__(self):
        super().__init__()
        self.title("AutomataLab - Lenguajes Formales")
        self.geometry("1200x750")
        self.minsize(900, 600)

        # Apply a modern style
        self._setup_style()

        # Title bar
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=10, pady=(8, 0))

        ttk.Label(title_frame, text="AutomataLab",
                   font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT)
        ttk.Label(title_frame,
                   text="Generador y verificador de lenguajes formales",
                   font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=15)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.dfa_tab = DFATab(self.notebook)
        self.nfa_tab = NFATab(self.notebook)
        self.pda_tab = PDATab(self.notebook)
        self.regex_tab = RegexTab(self.notebook)
        self.cfg_tab = CFGTab(self.notebook)
        self.tm_tab = TMTab(self.notebook)

        self.notebook.add(self.dfa_tab, text="  DFA  ")
        self.notebook.add(self.nfa_tab, text="  NFA  ")
        self.notebook.add(self.pda_tab, text="  PDA  ")
        self.notebook.add(self.regex_tab, text="  Regex  ")
        self.notebook.add(self.cfg_tab, text="  CFG  ")
        self.notebook.add(self.tm_tab, text="  Turing  ")

        # Keyboard shortcuts
        self.bind('<Control-b>', lambda e: self._build_current())
        self.bind('<Control-t>', lambda e: self._test_current())
        self.bind('<F5>', lambda e: self._build_current())

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        # Customize tab appearance
        style.configure('TNotebook.Tab', padding=[15, 6],
                         font=('Segoe UI', 10, 'bold'))
        style.configure('TButton', padding=[8, 4],
                         font=('Segoe UI', 9))
        style.configure('TLabel', font=('Segoe UI', 9))
        style.configure('TLabelframe.Label', font=('Segoe UI', 9, 'bold'))

    def _get_current_tab(self):
        idx = self.notebook.index(self.notebook.select())
        tabs = [self.dfa_tab, self.nfa_tab, self.pda_tab,
                self.regex_tab, self.cfg_tab, self.tm_tab]
        return tabs[idx]

    def _build_current(self):
        tab = self._get_current_tab()
        tab._on_build()

    def _test_current(self):
        tab = self._get_current_tab()
        tab._on_test()
