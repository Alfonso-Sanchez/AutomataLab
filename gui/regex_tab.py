"""Formal Regular Expression tab.

Provides a GUI for studying formal regular expressions as taught in
formal language theory courses. Supports parsing, Thompson's construction
(RE -> NFA), and string testing.

All UI text is in Spanish. This tab does NOT use Python regex --
it only supports formal RE operators: literal, epsilon, empty set,
union, concatenation, Kleene star, and Kleene plus.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

from core.regex_formal import FormalRegex
from gui.canvas_renderer import AutomataCanvas


# ---------------------------------------------------------------------------
# Syllabus examples (Sigma = {0,1} unless noted)
# ---------------------------------------------------------------------------

_EXAMPLES = [
    ("0*10*", "{0,1}", "Contiene exactamente un 1",
     "0\n1\n010\n00100\n11\n001\n100\n0010010"),
    ("(a\u222ab)*abb", "{a,b}", "Cadenas que terminan en abb",
     "abb\naabb\nbabb\naab\nabababb\nab\nbbbabb"),
    ("\u03a3*1\u03a3*", "{0,1}", "Al menos un 1",
     "1\n01\n10\n000\n0010\n111\n0\n"),
    ("\u03a3*001\u03a3*", "{0,1}", "Contiene 001 como subcadena",
     "001\n0010\n10011\n000\n111\n0001\n1001\n01"),
    ("(01\u207a)*", "{0,1}", "Cada 0 seguido de al menos un 1",
     "\n01\n011\n0101\n010\n0\n1\n01011"),
    ("(\u03a3\u03a3)*", "{0,1}", "Longitud par",
     "\n01\n0011\n000\n10\n101\n1010\n0"),
    ("(\u03a3\u03a3\u03a3)*", "{0,1}", "Longitud multiplo de 3",
     "\n010\n011010\n01\n0\n101010\n1010"),
    ("a*\u222ab*", "{a,b}", "Solo a's o solo b's",
     "\na\nb\naaa\nbbb\nab\nba\naba"),
]


class RegexTab(ttk.Frame):
    """Formal Regular Expression study tab."""

    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.nfa = None
        self.current_alphabet = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Main horizontal split
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- LEFT PANEL ---
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)
        self._build_left_panel(left_frame)

        # --- RIGHT PANEL ---
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=1)
        self._build_right_panel(right_frame)

        # --- STATUS BAR ---
        self.status_var = tk.StringVar(
            value="Escribe una expresion regular formal y presiona 'Construir'."
        )
        status_bar = ttk.Label(
            self, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W,
            font=('Segoe UI', 9)
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_left_panel(self, parent):
        # --- RE input section ---
        input_section = ttk.Frame(parent)
        input_section.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            input_section, text="Expresion Regular:",
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor=tk.W)

        # RE entry + build button row
        entry_row = ttk.Frame(input_section)
        entry_row.pack(fill=tk.X, pady=(3, 0))

        self.regex_entry = ttk.Entry(entry_row, font=('Consolas', 14))
        self.regex_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.regex_entry.bind('<Return>', lambda e: self._on_build())

        self.btn_build = ttk.Button(
            entry_row, text="Construir", command=self._on_build
        )
        self.btn_build.pack(side=tk.RIGHT)

        # Alphabet row
        alpha_row = ttk.Frame(input_section)
        alpha_row.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(alpha_row, text="Alfabeto:").pack(side=tk.LEFT)
        self.alpha_entry = ttk.Entry(alpha_row, font=('Consolas', 11), width=20)
        self.alpha_entry.pack(side=tk.LEFT, padx=5)
        self.alpha_entry.insert(0, "0, 1")
        ttk.Label(
            alpha_row, text="(auto si vacio)",
            font=('Segoe UI', 8, 'italic')
        ).pack(side=tk.LEFT)

        # Example selector row
        example_row = ttk.Frame(input_section)
        example_row.pack(fill=tk.X, pady=(5, 0))

        self.example_var = tk.StringVar(value="Ejemplo 1")
        example_values = [f"Ejemplo {i+1}" for i in range(len(_EXAMPLES))]
        self.example_menu = ttk.Combobox(
            example_row, textvariable=self.example_var,
            values=example_values, state='readonly', width=12
        )
        self.example_menu.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_load = ttk.Button(
            example_row, text="Cargar", command=self._load_example
        )
        self.btn_load.pack(side=tk.LEFT, padx=2)

        self.btn_clear = ttk.Button(
            example_row, text="Limpiar", command=self._clear_all
        )
        self.btn_clear.pack(side=tk.LEFT, padx=2)

        # --- Symbol insertion buttons ---
        sym_frame = ttk.Frame(input_section)
        sym_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(sym_frame, text="Insertar:").pack(side=tk.LEFT)
        for sym, tip in [("\u03b5", "epsilon"), ("\u2205", "vacio"),
                         ("\u222a", "union"), ("\u03a3", "sigma"),
                         ("\u207a", "plus"), ("*", "star")]:
            btn = ttk.Button(
                sym_frame, text=sym, width=3,
                command=lambda s=sym: self._insert_symbol(s)
            )
            btn.pack(side=tk.LEFT, padx=1)

        # --- Reference card ---
        ref_frame = ttk.LabelFrame(parent, text="Referencia (Temario)")
        ref_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.ref_text = scrolledtext.ScrolledText(
            ref_frame, wrap=tk.WORD, font=('Consolas', 9),
            bg='#1E1E1E', fg='#D4D4D4', state='normal',
            padx=8, pady=5
        )
        self.ref_text.pack(fill=tk.BOTH, expand=True)
        self._populate_reference()
        self.ref_text.config(state='disabled')

    def _build_right_panel(self, parent):
        right_paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        right_paned.pack(fill=tk.BOTH, expand=True)

        # --- NFA visualisation ---
        viz_frame = ttk.LabelFrame(parent, text="NFA Resultante (Thompson)")
        right_paned.add(viz_frame, weight=2)

        self.canvas = AutomataCanvas(viz_frame, width=450, height=300)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # --- Test section ---
        test_frame = ttk.LabelFrame(parent, text="Probar Cadenas")
        right_paned.add(test_frame, weight=1)

        # Single test row
        single_row = ttk.Frame(test_frame)
        single_row.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(single_row, text="Cadena:").pack(side=tk.LEFT)
        self.test_entry = ttk.Entry(single_row, font=('Consolas', 11))
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.test_entry.bind('<Return>', lambda e: self._on_test())

        ttk.Button(
            single_row, text="ε", width=2,
            command=lambda: self._insert_test_symbol("ε")
        ).pack(side=tk.LEFT, padx=1)

        self.btn_test = ttk.Button(
            single_row, text="Probar", command=self._on_test
        )
        self.btn_test.pack(side=tk.LEFT, padx=2)

        self.btn_batch = ttk.Button(
            single_row, text="Probar Lote", command=self._on_batch_test
        )
        self.btn_batch.pack(side=tk.LEFT, padx=2)

        # Batch input
        batch_frame = ttk.Frame(test_frame)
        batch_frame.pack(fill=tk.X, padx=5, pady=(0, 3))

        ttk.Label(batch_frame, text="Lote (una por linea):").pack(anchor=tk.W)
        self.batch_entry = scrolledtext.ScrolledText(
            batch_frame, wrap=tk.WORD, font=('Consolas', 10),
            height=4, bg='#2D2D2D', fg='#D4D4D4',
            insertbackground='white', padx=5, pady=3
        )
        self.batch_entry.pack(fill=tk.X)

        # Results
        self.results = scrolledtext.ScrolledText(
            test_frame, wrap=tk.WORD, font=('Consolas', 10),
            bg='#1A1A2E', fg='#E0E0E0',
            insertbackground='white', state='disabled',
            padx=8, pady=5
        )
        self.results.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Result tags
        self.results.tag_configure(
            'accepted', foreground='#4CAF50', font=('Consolas', 10, 'bold')
        )
        self.results.tag_configure(
            'rejected', foreground='#F44336', font=('Consolas', 10, 'bold')
        )
        self.results.tag_configure('error', foreground='#FF9800')
        self.results.tag_configure('info', foreground='#64B5F6')
        self.results.tag_configure(
            'step', foreground='#CE93D8', font=('Consolas', 10)
        )

    # ------------------------------------------------------------------
    # Reference card content
    # ------------------------------------------------------------------

    def _populate_reference(self):
        t = self.ref_text
        t.tag_configure('heading', foreground='#64B5F6',
                        font=('Consolas', 9, 'bold'))
        t.tag_configure('example', foreground='#81C784')
        t.tag_configure('identity', foreground='#CE93D8')

        t.insert(tk.END, "OPERADORES FORMALES:\n", 'heading')
        t.insert(tk.END,
                 "  a         Literal (a \u2208 \u03a3)\n"
                 "  \u03b5         Cadena vacia (epsilon)\n"
                 "  \u2205         Conjunto vacio\n"
                 "  R\u2081\u222aR\u2082     Union\n"
                 "  R\u2081R\u2082      Concatenacion\n"
                 "  R*        Cerradura de Kleene\n"
                 "  R\u207a        Cerradura positiva (= RR*)\n"
                 "  \u03a3         Alfabeto completo\n\n")

        t.insert(tk.END, "PRECEDENCIA: ", 'heading')
        t.insert(tk.END, "* > \u25e6 (concat) > \u222a (union)\n")
        t.insert(tk.END, "  a\u222ab\u25e6c* = a\u222a(b\u25e6(c*))\n\n")

        t.insert(tk.END, "IDENTIDADES:\n", 'heading')
        t.insert(tk.END,
                 "  R\u222a\u2205 = R\n"
                 "  R\u25e6\u03b5 = R\n"
                 "  1*\u2205 = \u2205\n"
                 "  \u2205* = \u03b5\n"
                 "  \u03b5* = \u03b5\n\n", 'identity')

        t.insert(tk.END, "EJEMPLOS DEL TEMARIO (\u03a3={0,1}):\n", 'heading')
        t.insert(tk.END,
                 "  0*10*       un solo 1\n"
                 "  \u03a3*1\u03a3*      al menos un 1\n"
                 "  \u03a3*001\u03a3*    contiene 001\n"
                 "  (01\u207a)*      no inicia con 1,\n"
                 "              cada 0 seguido de 1+\n"
                 "  (\u03a3\u03a3)*       longitud par\n"
                 "  (\u03a3\u03a3\u03a3)*      longitud multiplo de 3\n",
                 'example')

    # ------------------------------------------------------------------
    # Symbol insertion
    # ------------------------------------------------------------------

    def _insert_symbol(self, sym):
        self.regex_entry.insert(tk.INSERT, sym)
        self.regex_entry.focus_set()

    def _insert_test_symbol(self, sym):
        self.test_entry.insert(tk.INSERT, sym)
        self.test_entry.focus_set()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_result(self, text, tag=None):
        self.results.config(state='normal')
        if tag:
            self.results.insert(tk.END, text, tag)
        else:
            self.results.insert(tk.END, text)
        self.results.see(tk.END)
        self.results.config(state='disabled')

    def _clear_results(self):
        self.results.config(state='normal')
        self.results.delete('1.0', tk.END)
        self.results.config(state='disabled')

    def _get_alphabet(self):
        """Parse the alphabet entry, return list of symbols or None for auto."""
        raw = self.alpha_entry.get().strip()
        if not raw:
            return None
        # Accept: "0, 1" or "0,1" or "a b c" or "a,b,c" or "{0,1}"
        raw = raw.strip('{}')
        if ',' in raw:
            symbols = [s.strip() for s in raw.split(',') if s.strip()]
        else:
            symbols = raw.split()
        return symbols if symbols else None

    def _clear_all(self):
        self.regex_entry.delete(0, tk.END)
        self.test_entry.delete(0, tk.END)
        self.batch_entry.delete('1.0', tk.END)
        self._clear_results()
        self.canvas.clear()
        self.tree = None
        self.nfa = None
        self.status_var.set("Limpiado.")

    # ------------------------------------------------------------------
    # Example loading
    # ------------------------------------------------------------------

    def _load_example(self):
        choice = self.example_var.get()
        try:
            idx = int(choice.split()[-1]) - 1
        except (ValueError, IndexError):
            idx = 0
        if idx < 0 or idx >= len(_EXAMPLES):
            idx = 0

        expr, alpha, desc, batch = _EXAMPLES[idx]

        self.regex_entry.delete(0, tk.END)
        self.regex_entry.insert(0, expr)

        self.alpha_entry.delete(0, tk.END)
        self.alpha_entry.insert(0, alpha)

        self.batch_entry.delete('1.0', tk.END)
        self.batch_entry.insert('1.0', batch)

        self.status_var.set(f"Ejemplo cargado: {expr}  ({desc})")

    # ------------------------------------------------------------------
    # Build (parse + Thompson's construction)
    # ------------------------------------------------------------------

    def _on_build(self):
        expr_str = self.regex_entry.get().strip()
        if not expr_str:
            self.status_var.set("Ingresa una expresion regular formal")
            return

        alphabet = self._get_alphabet()
        tree, errors = FormalRegex.parse(expr_str, alphabet)

        if errors:
            self.tree = None
            self.nfa = None
            self.status_var.set(f"Error: {'; '.join(errors)}")
            self._clear_results()
            self._write_result("ERRORES DE PARSEO:\n", 'error')
            for e in errors:
                self._write_result(f"  - {e}\n", 'error')
            return

        self.tree = tree

        # Build NFA via Thompson's construction
        nfa = FormalRegex.to_nfa(tree, alphabet)
        self.nfa = nfa

        # Auto-detect alphabet if not given
        detected = FormalRegex.auto_detect_alphabet(tree)
        self.current_alphabet = alphabet if alphabet else detected

        # Update alphabet entry to show detected
        if not alphabet:
            self.alpha_entry.delete(0, tk.END)
            self.alpha_entry.insert(0, ', '.join(detected))

        # Render NFA on canvas
        labels = nfa.get_transition_labels()
        self.canvas.render_automaton(
            nfa.states, nfa.initial_state, nfa.accept_states, labels
        )

        # Show info in results
        canonical = FormalRegex.tree_to_string(tree)
        has_eps = any(s == '\u03b5' for (_, s) in nfa.transitions.keys())
        total_trans = sum(len(v) for v in nfa.transitions.values())

        self.status_var.set(
            f"NFA construido: {len(nfa.states)} estados, "
            f"{total_trans} transiciones"
            f"{', con \u03b5-transiciones' if has_eps else ''}"
        )

        self._clear_results()
        self._write_result("Construccion de Thompson exitosa.\n\n", 'info')
        self._write_result(f"  Expresion:   {expr_str}\n")
        self._write_result(f"  Canonica:    {canonical}\n")
        self._write_result(f"  Alfabeto:    {{{', '.join(nfa.alphabet)}}}\n")
        self._write_result(f"  Estados:     {len(nfa.states)}\n")
        self._write_result(f"  Transiciones:{total_trans}\n")
        self._write_result(f"  Inicial:     {nfa.initial_state}\n")
        self._write_result(
            f"  Aceptacion:  {{{', '.join(sorted(nfa.accept_states))}}}\n"
        )
        if has_eps:
            closure = nfa.epsilon_closure({nfa.initial_state})
            self._write_result(
                f"  \u03b5-clausura({nfa.initial_state}): "
                f"{{{', '.join(sorted(closure))}}}\n"
            )
        self._write_result("\nListo para probar cadenas.\n")

    # ------------------------------------------------------------------
    # Single string test
    # ------------------------------------------------------------------

    def _on_test(self):
        if self.nfa is None:
            self.status_var.set("Primero construye el NFA (presiona 'Construir')")
            return

        input_str = self.test_entry.get()
        self._clear_results()

        display = input_str if input_str else '\u03b5 (cadena vacia)'
        expr_str = self.regex_entry.get().strip()
        self._write_result(f"Regex: {expr_str}\n", 'info')
        self._write_result(f"Cadena: \"{display}\"\n")
        self._write_result(f"{'=' * 40}\n\n")

        accepted, trace, msg = self.nfa.test(input_str)

        # Show trace
        if trace:
            self._write_result("Traza de conjuntos de estados:\n", 'step')
            for i, (states, symbol) in enumerate(trace):
                states_str = '{' + ', '.join(sorted(states)) + '}'
                if i == 0:
                    self._write_result(
                        f"  Inicio (\u03b5-clausura): {states_str}\n"
                    )
                else:
                    self._write_result(f"  Lee '{symbol}': {states_str}\n")
            self._write_result('\n')

        tag = 'accepted' if accepted else 'rejected'
        self._write_result(f"Resultado: {msg}\n", tag)

        # Highlight final states on canvas
        if trace:
            final_states = set(trace[-1][0])
            hl_type = 'accept' if accepted else 'reject'
            labels = self.nfa.get_transition_labels()
            self.canvas.render_automaton(
                self.nfa.states, self.nfa.initial_state,
                self.nfa.accept_states, labels,
                highlighted=final_states, highlight_type=hl_type
            )

        self.status_var.set(
            f"{'ACEPTADA' if accepted else 'RECHAZADA'}: \"{display}\""
        )

    # ------------------------------------------------------------------
    # Batch test
    # ------------------------------------------------------------------

    def _on_batch_test(self):
        if self.nfa is None:
            self.status_var.set("Primero construye el NFA (presiona 'Construir')")
            return

        text = self.batch_entry.get('1.0', tk.END).strip()
        if not text:
            self.status_var.set("Ingresa cadenas en el area de lote")
            return

        # Each line is a string to test; empty line = epsilon
        lines = text.split('\n')
        strings = []
        for line in lines:
            s = line.rstrip('\r')
            strings.append(s)

        expr_str = self.regex_entry.get().strip()
        self._clear_results()
        self._write_result(f"Regex: {expr_str}\n", 'info')
        self._write_result(f"Probando {len(strings)} cadenas:\n")
        self._write_result(f"{'=' * 40}\n\n")

        accepted_count = 0
        for s in strings:
            accepted, trace, msg = self.nfa.test(s)
            display = s if s else '\u03b5'
            if accepted:
                self._write_result("  ACEPTA  ", 'accepted')
                accepted_count += 1
            else:
                self._write_result("  RECHAZA ", 'rejected')
            self._write_result(f"\"{display}\"\n")

        self._write_result(
            f"\nResumen: {accepted_count}/{len(strings)} aceptadas\n", 'info'
        )
        self.status_var.set(
            f"Lote: {accepted_count}/{len(strings)} aceptadas"
        )

    # ------------------------------------------------------------------
    # Compatibility stubs (called by app.py keyboard shortcuts)
    # ------------------------------------------------------------------

    def _on_step(self):
        self._on_test()
