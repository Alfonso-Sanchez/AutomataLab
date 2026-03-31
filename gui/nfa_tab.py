"""NFA interactive editor tab."""

import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox

from gui.canvas_renderer import AutomataCanvas
from core.nfa import NFA


class NFATransitionDialog(tk.Toplevel):
    """Custom dialog for NFA transition input with epsilon button."""

    def __init__(self, parent, from_state, to_state):
        super().__init__(parent)
        self.title('Transicion NFA')
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(False, False)

        self.result = None

        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f'Transicion: {from_state} \u2192 {to_state}',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        row = ttk.Frame(main)
        row.pack(fill=tk.X, pady=5)

        ttk.Label(row, text='Simbolo:').pack(side=tk.LEFT)
        self.symbol_entry = ttk.Entry(row, font=('Consolas', 11), width=15)
        self.symbol_entry.pack(side=tk.LEFT, padx=(5, 3))
        ttk.Button(row, text='\u03b5', width=2,
                   command=self._insert_epsilon).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=(12, 0))

        ttk.Button(btn_frame, text='Aceptar', command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Cancelar', command=self._on_cancel).pack(side=tk.LEFT, padx=5)

        self.symbol_entry.focus_set()
        self.bind('<Return>', lambda e: self._on_ok())
        self.bind('<Escape>', lambda e: self._on_cancel())

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_toplevel()
        x = pw.winfo_x() + (pw.winfo_width() - self.winfo_width()) // 2
        y = pw.winfo_y() + (pw.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')

    def _insert_epsilon(self):
        self.symbol_entry.insert(tk.INSERT, '\u03b5')
        self.symbol_entry.focus_set()

    def _on_ok(self):
        symbol = self.symbol_entry.get().strip()
        if not symbol:
            self.result = None
            self.destroy()
            return
        if symbol.lower() in ('eps', 'epsilon', 'e'):
            symbol = '\u03b5'
        self.result = symbol
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class NFATab(ttk.Frame):
    """Interactive NFA builder and tester tab."""

    def __init__(self, parent):
        super().__init__(parent)
        self.nfa = None
        self._step_index = 0
        self._step_trace = []
        self._step_string = ""
        self._build_ui()

    # ──────────────────────────────────────────────
    # UI Construction
    # ──────────────────────────────────────────────

    def _build_ui(self):
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Left panel: Interactive canvas ---
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=3)

        self.canvas = AutomataCanvas(left_frame, width=500, height=400)
        self.canvas.automaton_type = 'NFA'
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.set_transition_dialog(self._transition_dialog)
        self.canvas.set_on_change(self._on_canvas_change)

        # Extra buttons row
        extra_bar = ttk.Frame(left_frame)
        extra_bar.pack(fill=tk.X, pady=(2, 0))

        ttk.Label(extra_bar, text='Ejemplo:').pack(side=tk.LEFT, padx=(0, 2))
        self._example_var = tk.StringVar(value='Seleccionar...')
        example_combo = ttk.Combobox(extra_bar, textvariable=self._example_var,
                                     values=['Termina en "ab"', 'NFA con epsilon'],
                                     state='readonly', width=18)
        example_combo.pack(side=tk.LEFT, padx=2)
        example_combo.bind('<<ComboboxSelected>>', self._on_example_selected)

        ttk.Button(extra_bar, text='Importar',
                   command=self._on_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(extra_bar, text='Exportar',
                   command=self._on_export).pack(side=tk.RIGHT, padx=2)

        # --- Right panel: Testing + Formal Definition ---
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)

        self._right_notebook = ttk.Notebook(right_frame)
        self._right_notebook.pack(fill=tk.BOTH, expand=True)

        # === Tab 1: Ejecucion ===
        exec_frame = ttk.Frame(self._right_notebook)
        self._right_notebook.add(exec_frame, text='Ejecucion')

        ttk.Label(exec_frame, text='Probar Cadenas',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=(5, 2))

        input_frame = ttk.Frame(exec_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(input_frame, text='Cadena:').pack(side=tk.LEFT)
        self.test_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.test_entry.bind('<Return>', lambda e: self._on_test())

        ttk.Button(input_frame, text='Probar',
                   command=self._on_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_frame, text='Paso a paso',
                   command=self._on_step).pack(side=tk.LEFT, padx=2)

        self.results = scrolledtext.ScrolledText(
            exec_frame, wrap=tk.WORD, font=('Consolas', 10),
            bg='#1A1A2E', fg='#E0E0E0',
            insertbackground='white', state='disabled',
            padx=8, pady=5
        )
        self.results.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))

        self.results.tag_configure('accepted', foreground='#4CAF50',
                                   font=('Consolas', 10, 'bold'))
        self.results.tag_configure('rejected', foreground='#F44336',
                                   font=('Consolas', 10, 'bold'))
        self.results.tag_configure('error', foreground='#FF9800')
        self.results.tag_configure('info', foreground='#64B5F6')
        self.results.tag_configure('step', foreground='#CE93D8')

        # === Tab 2: Definicion Formal + Tabla δ ===
        info_frame = ttk.Frame(self._right_notebook)
        self._right_notebook.add(info_frame, text='Definicion / Tabla \u03b4')

        self._info_text = scrolledtext.ScrolledText(
            info_frame, wrap=tk.WORD, font=('Consolas', 10),
            bg='#1A1A2E', fg='#E0E0E0', state='disabled',
            padx=8, pady=5
        )
        self._info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._info_text.tag_configure('title', foreground='#FFD54F',
                                       font=('Consolas', 11, 'bold'))
        self._info_text.tag_configure('formal', foreground='#80CBC4',
                                       font=('Consolas', 10))
        self._info_text.tag_configure('header', foreground='#CE93D8',
                                       font=('Consolas', 10, 'bold'))
        self._info_text.tag_configure('accept_st', foreground='#4CAF50',
                                       font=('Consolas', 10, 'bold'))
        self._info_text.tag_configure('row', foreground='#E0E0E0',
                                       font=('Consolas', 10))

        self.status_var = tk.StringVar(value='Listo. Agrega estados con la barra de herramientas.')
        ttk.Label(self, textvariable=self.status_var,
                  relief=tk.SUNKEN, anchor=tk.W,
                  font=('Segoe UI', 9)).pack(fill=tk.X, side=tk.BOTTOM)

    # ──────────────────────────────────────────────
    # Transition dialog (NFA-specific)
    # ──────────────────────────────────────────────

    def _transition_dialog(self, from_state, to_state):
        """Open custom dialog for NFA transition with epsilon button."""
        dlg = NFATransitionDialog(self, from_state, to_state)
        self.wait_window(dlg)
        return dlg.result

    # ──────────────────────────────────────────────
    # Canvas change
    # ──────────────────────────────────────────────

    def _on_canvas_change(self):
        n_states = len(self.canvas.states)
        n_trans = len(self.canvas.transitions)
        self.status_var.set(f'NFA: {n_states} estados, {n_trans} transiciones')
        self.nfa = None
        self._update_info_tab()

    # ──────────────────────────────────────────────
    # Formal definition tab
    # ──────────────────────────────────────────────

    def _update_info_tab(self):
        """Populate the formal definition and transition table tab."""
        if not self.canvas.states:
            t = self._info_text
            t.config(state='normal')
            t.delete('1.0', tk.END)
            t.insert(tk.END, '(Agrega estados al canvas para ver la definicion formal)\n', 'row')
            t.config(state='disabled')
            return
        nfa = self._build_nfa_from_canvas()

        t = self._info_text
        t.config(state='normal')
        t.delete('1.0', tk.END)

        t.insert(tk.END, 'Definicion Formal\n', 'title')
        t.insert(tk.END, '\u2500' * 36 + '\n', 'header')
        t.insert(tk.END, nfa.get_formal_definition() + '\n\n', 'formal')

        t.insert(tk.END, 'Tabla de Transiciones  \u03b4(q, a) = {Q\'}\n', 'title')
        t.insert(tk.END, '\u2500' * 36 + '\n', 'header')

        rows = nfa.get_transition_table()
        if rows:
            col_w = max((len(r[0]) for r in rows), default=5)
            col_w = max(col_w, 5)
            header_line = f"  {'Estado':<{col_w}}  {'Lee':<5}  {'->':>2}  Destinos\n"
            t.insert(tk.END, header_line, 'header')
            t.insert(tk.END, '  ' + '-' * (col_w + 22) + '\n', 'header')
            for from_s, symbol, to_states in rows:
                dest = '{' + ', '.join(sorted(to_states)) + '}'
                has_acc = bool(to_states & nfa.accept_states)
                line = f"  {from_s:<{col_w}}  {symbol:<5}  {'->':>2}  {dest}\n"
                t.insert(tk.END, line, 'accept_st' if has_acc else 'row')
        else:
            t.insert(tk.END, '  (sin transiciones)\n', 'row')

        closures = nfa.get_epsilon_closures()
        if closures:
            t.insert(tk.END, '\n\u03b5-clausuras\n', 'title')
            t.insert(tk.END, '\u2500' * 36 + '\n', 'header')
            for state, closure in sorted(closures.items()):
                cl_str = '{' + ', '.join(sorted(closure)) + '}'
                t.insert(tk.END, f'  \u03b5-cl({state}) = {cl_str}\n', 'formal')

        t.config(state='disabled')

    # ──────────────────────────────────────────────
    # Build NFA from canvas
    # ──────────────────────────────────────────────

    def _build_nfa_from_canvas(self):
        nfa = NFA()
        nfa.states = list(self.canvas.states.keys())
        for name, data in self.canvas.states.items():
            if data['is_initial']:
                nfa.initial_state = name
            if data['is_accept']:
                nfa.accept_states.add(name)
        for t in self.canvas.transitions:
            key = (t['from'], t['label'])
            if key not in nfa.transitions:
                nfa.transitions[key] = set()
            nfa.transitions[key].add(t['to'])
            if t['label'] != '\u03b5' and t['label'] not in nfa.alphabet:
                nfa.alphabet.append(t['label'])
        return nfa

    def _on_build(self):
        if not self.canvas.states:
            self.status_var.set('No hay estados definidos')
            return
        nfa = self._build_nfa_from_canvas()
        if nfa.initial_state is None:
            self.status_var.set('Error: No hay estado inicial definido')
            self._clear_results()
            self._write_result('No hay estado inicial. Usa el modo "Inicial" para asignar uno.\n', 'error')
            return
        self.nfa = nfa
        has_epsilon = any(s == '\u03b5' for (_, s) in nfa.transitions.keys())
        total_trans = sum(len(v) for v in nfa.transitions.values())
        self.status_var.set(
            f'NFA construido: {len(nfa.states)} estados, '
            f'{total_trans} transiciones'
            f'{", con \u03b5-transiciones" if has_epsilon else ""}'
        )
        self._clear_results()
        self._write_result('NFA construido exitosamente.\n', 'info')
        self._write_result(f'  Estados: {", ".join(nfa.states)}\n')
        self._write_result(f'  Inicial: {nfa.initial_state}\n')
        self._write_result(f'  Aceptacion: {", ".join(nfa.accept_states)}\n')
        self._write_result(f'  Alfabeto: {{{", ".join(nfa.alphabet)}}}\n')
        if has_epsilon:
            closure = nfa.epsilon_closure({nfa.initial_state})
            self._write_result(f'  \u03b5-clausura({nfa.initial_state}): {{{", ".join(sorted(closure))}}}\n')

    # ──────────────────────────────────────────────
    # Examples
    # ──────────────────────────────────────────────

    def _on_example_selected(self, event=None):
        choice = self._example_var.get()
        if 'ab' in choice.lower():
            text = NFA.example()
        else:
            text = NFA.example2()
        nfa, errors = NFA.parse(text)
        if nfa and not errors:
            labels = nfa.get_transition_labels()
            self.canvas.load_from_model(nfa.states, nfa.initial_state,
                                        nfa.accept_states, labels)
            self.nfa = nfa
            self.status_var.set(f'Ejemplo cargado: {len(nfa.states)} estados')
            self._clear_results()
            self._write_result('Ejemplo cargado en el canvas.\n', 'info')
            self._update_info_tab()

    # ──────────────────────────────────────────────
    # Import / Export
    # ──────────────────────────────────────────────

    def _on_import(self):
        win = tk.Toplevel(self)
        win.title('Importar NFA desde texto')
        win.geometry('620x450')
        win.minsize(500, 350)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Pega la definicion del NFA:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def do_import():
            text = editor.get('1.0', tk.END)
            nfa, errors = NFA.parse(text)
            if errors:
                messagebox.showerror('Errores de parseo', '\n'.join(errors), parent=win)
                return
            labels = nfa.get_transition_labels()
            self.canvas.load_from_model(nfa.states, nfa.initial_state,
                                        nfa.accept_states, labels)
            self.nfa = nfa
            self.status_var.set(f'NFA importado: {len(nfa.states)} estados')
            self._clear_results()
            self._write_result('NFA importado exitosamente desde texto.\n', 'info')
            self._update_info_tab()
            win.destroy()

        ttk.Button(btn_frame, text='Importar', command=do_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cancelar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_export(self):
        if not self.canvas.states:
            messagebox.showinfo('Exportar', 'No hay automata para exportar.', parent=self)
            return

        nfa = self._build_nfa_from_canvas()
        lines = []
        lines.append(f'States: {", ".join(nfa.states)}')
        lines.append(f'Alphabet: {", ".join(nfa.alphabet)}')
        lines.append(f'Initial: {nfa.initial_state or ""}')
        lines.append(f'Accept: {", ".join(sorted(nfa.accept_states))}')
        lines.append('Transitions:')
        for (from_s, symbol), to_states in sorted(nfa.transitions.items()):
            lines.append(f'{from_s}, {symbol} -> {", ".join(sorted(to_states))}')
        text = '\n'.join(lines)

        win = tk.Toplevel(self)
        win.title('Exportar NFA como texto')
        win.geometry('620x400')
        win.minsize(500, 300)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Definicion del NFA:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))

        def copy_all():
            win.clipboard_clear()
            win.clipboard_append(text)
            self.status_var.set('Definicion copiada al portapapeles')

        ttk.Button(btn_frame, text='Copiar', command=copy_all).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cerrar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        editor.insert('1.0', text)

    # ──────────────────────────────────────────────
    # Testing
    # ──────────────────────────────────────────────

    def _on_test(self):
        if self.nfa is None:
            if not self.canvas.states:
                self.status_var.set('No hay automata definido')
                return
            self.nfa = self._build_nfa_from_canvas()

        if self.nfa.initial_state is None:
            self.status_var.set('No hay estado inicial definido')
            self._clear_results()
            self._write_result('Error: No hay estado inicial definido.\n', 'error')
            return

        input_str = self.test_entry.get()
        self._clear_results()
        accepted, trace, msg = self.nfa.test(input_str)

        display_str = input_str if input_str else '\u03b5 (cadena vacia)'
        self._write_result(f'Probando: "{display_str}"\n\n', 'info')

        if trace:
            self._write_result('Traza de conjuntos de estados:\n', 'step')
            for i, (states, symbol) in enumerate(trace):
                states_str = '{' + ', '.join(sorted(states)) + '}'
                if i == 0:
                    self._write_result(f'  Inicio (\u03b5-clausura): {states_str}\n')
                else:
                    self._write_result(f'  Lee \'{symbol}\': {states_str}\n')
            self._write_result('\n')

        tag = 'accepted' if accepted else 'rejected'
        self._write_result(f'Resultado: {msg}\n', tag)

        if trace:
            final_states = set(trace[-1][0])
            hl_type = 'accept' if accepted else 'reject'
            self.canvas.highlight_states(final_states, hl_type)

    def _on_step(self):
        """Step-by-step NFA simulation showing sets of states."""
        if self.nfa is None:
            if not self.canvas.states:
                self.status_var.set('No hay automata definido')
                return
            self.nfa = self._build_nfa_from_canvas()

        if self.nfa.initial_state is None:
            self.status_var.set('No hay estado inicial definido')
            return

        input_str = self.test_entry.get()

        if self._step_string != input_str or self._step_index >= len(input_str) + 1:
            self._step_string = input_str
            self._step_index = 0
            _, trace, _ = self.nfa.test(input_str)
            self._step_trace = trace
            self._clear_results()
            display_str = input_str if input_str else '\u03b5'
            self._write_result(f'Simulacion paso a paso: "{display_str}"\n', 'info')
            self._write_result(f'{"=" * 40}\n\n')

        if self._step_index < len(self._step_trace):
            states, symbol = self._step_trace[self._step_index]
            states_str = '{' + ', '.join(sorted(states)) + '}'

            if self._step_index == 0:
                self._write_result(f'Paso 0: \u03b5-clausura inicial = {states_str}\n', 'step')
                self._write_result(f'  Cadena restante: "{input_str}"\n\n')
            else:
                remaining = input_str[self._step_index:]
                self._write_result(
                    f'Paso {self._step_index}: Lee \'{symbol}\' -> {states_str}\n', 'step')
                self._write_result(f'  Cadena restante: "{remaining}"\n\n')

            hl_type = 'normal'
            if self._step_index == len(self._step_trace) - 1:
                accepted = bool(set(states) & self.nfa.accept_states)
                hl_type = 'accept' if accepted else 'reject'
            self.canvas.highlight_states(set(states), hl_type)

            self._step_index += 1

            if self._step_index >= len(self._step_trace):
                final_states = set(self._step_trace[-1][0])
                accepted = bool(final_states & self.nfa.accept_states)
                tag = 'accepted' if accepted else 'rejected'
                msg = 'ACEPTADA' if accepted else 'RECHAZADA'
                self._write_result(f'\nResultado final: {msg}\n', tag)
        else:
            self._step_string = ''
            self._on_step()

    # ──────────────────────────────────────────────
    # Result helpers
    # ──────────────────────────────────────────────

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
