"""DFA interactive editor tab."""

import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox

from gui.canvas_renderer import AutomataCanvas
from core.dfa import DFA


class DFATab(ttk.Frame):
    """Interactive DFA builder and tester tab."""

    def __init__(self, parent):
        super().__init__(parent)
        self.dfa = None
        self._step_index = 0
        self._step_path = []
        self._step_string = ""
        self._build_ui()

    # ──────────────────────────────────────────────
    # UI Construction
    # ──────────────────────────────────────────────

    def _build_ui(self):
        # Main horizontal paned window
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Left panel: Interactive canvas ---
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=3)

        # Canvas with integrated toolbar
        self.canvas = AutomataCanvas(left_frame, width=500, height=400)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.set_transition_dialog(self._transition_dialog)
        self.canvas.set_on_change(self._on_canvas_change)

        # Extra buttons row below canvas
        extra_bar = ttk.Frame(left_frame)
        extra_bar.pack(fill=tk.X, pady=(2, 0))

        # Example dropdown
        ttk.Label(extra_bar, text='Ejemplo:').pack(side=tk.LEFT, padx=(0, 2))
        self._example_var = tk.StringVar(value='Seleccionar...')
        example_combo = ttk.Combobox(extra_bar, textvariable=self._example_var,
                                     values=['Binarios div 3', 'Contiene "aba"'],
                                     state='readonly', width=18)
        example_combo.pack(side=tk.LEFT, padx=2)
        example_combo.bind('<<ComboboxSelected>>', self._on_example_selected)

        ttk.Separator(extra_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Button(extra_bar, text='Importar texto',
                   command=self._on_import).pack(side=tk.LEFT, padx=2)
        ttk.Button(extra_bar, text='Exportar texto',
                   command=self._on_export).pack(side=tk.LEFT, padx=2)

        # --- Right panel: Testing ---
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)

        test_label = ttk.Label(right_frame, text='Probar Cadenas',
                               font=('Segoe UI', 10, 'bold'))
        test_label.pack(anchor=tk.W, padx=5, pady=(5, 2))

        # Input row
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(input_frame, text='Cadena:').pack(side=tk.LEFT)
        self.test_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.test_entry.bind('<Return>', lambda e: self._on_test())

        ttk.Button(input_frame, text='Probar',
                   command=self._on_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_frame, text='Paso a paso',
                   command=self._on_step).pack(side=tk.LEFT, padx=2)

        # Results area
        self.results = scrolledtext.ScrolledText(
            right_frame, wrap=tk.WORD, font=('Consolas', 10),
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

        # Status bar
        self.status_var = tk.StringVar(value='Listo. Agrega estados con la barra de herramientas.')
        status_bar = ttk.Label(self, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W,
                               font=('Segoe UI', 9))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Keyboard shortcut
        self.bind_all_for_tab('<Control-b>', self._on_build)

    def bind_all_for_tab(self, sequence, handler):
        """Bind keyboard shortcut scoped to this tab's widgets."""
        self.bind(sequence, lambda e: handler())
        # Also bind on canvas and entry so it works when they have focus
        try:
            self.canvas.bind(sequence, lambda e: handler())
            self.test_entry.bind(sequence, lambda e: handler())
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Transition dialog
    # ──────────────────────────────────────────────

    def _transition_dialog(self, from_state, to_state):
        """Prompt user for DFA transition symbol."""
        symbol = simpledialog.askstring(
            'Transicion DFA',
            f'Simbolo para {from_state} \u2192 {to_state}:\n'
            '(un solo simbolo por transicion)',
            parent=self
        )
        if symbol is None:
            return None
        symbol = symbol.strip()
        if len(symbol) != 1:
            messagebox.showwarning('Simbolo invalido',
                                   'Un DFA requiere exactamente un simbolo por transicion.',
                                   parent=self)
            return None
        # Check if transition already exists for this (state, symbol)
        for t in self.canvas.transitions:
            if t['from'] == from_state and t['label'] == symbol:
                messagebox.showwarning('Transicion duplicada',
                                       f'Ya existe una transicion desde {from_state} con simbolo "{symbol}".\n'
                                       'En un DFA, cada par (estado, simbolo) tiene un unico destino.',
                                       parent=self)
                return None
        return symbol

    # ──────────────────────────────────────────────
    # Canvas change handler
    # ──────────────────────────────────────────────

    def _on_canvas_change(self):
        """Called when the canvas model changes."""
        n_states = len(self.canvas.states)
        n_trans = len(self.canvas.transitions)
        self.status_var.set(f'DFA: {n_states} estados, {n_trans} transiciones')
        # Auto-sync the internal DFA
        self.dfa = None  # Invalidate, will rebuild on test

    # ──────────────────────────────────────────────
    # Build DFA from canvas
    # ──────────────────────────────────────────────

    def _build_dfa_from_canvas(self):
        """Construct a DFA core object from the canvas data."""
        dfa = DFA()
        dfa.states = list(self.canvas.states.keys())
        for name, data in self.canvas.states.items():
            if data['is_initial']:
                dfa.initial_state = name
            if data['is_accept']:
                dfa.accept_states.add(name)
        for t in self.canvas.transitions:
            dfa.transitions[(t['from'], t['label'])] = t['to']
            if t['label'] not in dfa.alphabet:
                dfa.alphabet.append(t['label'])
        return dfa

    def _on_build(self):
        """Build/sync DFA from canvas data."""
        if not self.canvas.states:
            self.status_var.set('No hay estados definidos')
            return
        dfa = self._build_dfa_from_canvas()
        if dfa.initial_state is None:
            self.status_var.set('Error: No hay estado inicial definido')
            self._clear_results()
            self._write_result('No hay estado inicial. Usa el modo "Inicial" para asignar uno.\n', 'error')
            return
        self.dfa = dfa
        self.status_var.set(
            f'DFA construido: {len(dfa.states)} estados, '
            f'{len(dfa.transitions)} transiciones, '
            f'alfabeto: {{{", ".join(dfa.alphabet)}}}'
        )
        self._clear_results()
        self._write_result('DFA construido exitosamente.\n', 'info')
        self._write_result(f'  Estados: {", ".join(dfa.states)}\n')
        self._write_result(f'  Inicial: {dfa.initial_state}\n')
        self._write_result(f'  Aceptacion: {", ".join(dfa.accept_states)}\n')
        self._write_result(f'  Alfabeto: {{{", ".join(dfa.alphabet)}}}\n')

    # ──────────────────────────────────────────────
    # Examples
    # ──────────────────────────────────────────────

    def _on_example_selected(self, event=None):
        choice = self._example_var.get()
        if 'div' in choice.lower() or 'Binarios' in choice:
            text = DFA.example()
        else:
            text = DFA.example2()
        dfa, errors = DFA.parse(text)
        if dfa and not errors:
            labels = dfa.get_transition_labels()
            self.canvas.load_from_model(dfa.states, dfa.initial_state,
                                        dfa.accept_states, labels)
            self.dfa = dfa
            self.status_var.set(f'Ejemplo cargado: {len(dfa.states)} estados')
            self._clear_results()
            self._write_result('Ejemplo cargado en el canvas.\n', 'info')

    # ──────────────────────────────────────────────
    # Import / Export
    # ──────────────────────────────────────────────

    def _on_import(self):
        """Open a dialog to import a text definition."""
        win = tk.Toplevel(self)
        win.title('Importar DFA desde texto')
        win.geometry('500x400')
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Pega la definicion del DFA:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def do_import():
            text = editor.get('1.0', tk.END)
            dfa, errors = DFA.parse(text)
            if errors:
                messagebox.showerror('Errores de parseo',
                                     '\n'.join(errors), parent=win)
                return
            labels = dfa.get_transition_labels()
            self.canvas.load_from_model(dfa.states, dfa.initial_state,
                                        dfa.accept_states, labels)
            self.dfa = dfa
            self.status_var.set(f'DFA importado: {len(dfa.states)} estados')
            self._clear_results()
            self._write_result('DFA importado exitosamente desde texto.\n', 'info')
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text='Importar', command=do_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cancelar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_export(self):
        """Show the current automaton as text definition."""
        if not self.canvas.states:
            messagebox.showinfo('Exportar', 'No hay automata para exportar.', parent=self)
            return

        dfa = self._build_dfa_from_canvas()
        lines = []
        lines.append(f'States: {", ".join(dfa.states)}')
        lines.append(f'Alphabet: {", ".join(dfa.alphabet)}')
        lines.append(f'Initial: {dfa.initial_state or ""}')
        lines.append(f'Accept: {", ".join(sorted(dfa.accept_states))}')
        lines.append('Transitions:')
        for (from_s, symbol), to_s in sorted(dfa.transitions.items()):
            lines.append(f'{from_s}, {symbol} -> {to_s}')
        text = '\n'.join(lines)

        win = tk.Toplevel(self)
        win.title('Exportar DFA como texto')
        win.geometry('500x350')
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Definicion del DFA:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        editor.insert('1.0', text)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def copy_all():
            win.clipboard_clear()
            win.clipboard_append(text)
            self.status_var.set('Definicion copiada al portapapeles')

        ttk.Button(btn_frame, text='Copiar', command=copy_all).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cerrar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

    # ──────────────────────────────────────────────
    # Testing
    # ──────────────────────────────────────────────

    def _on_test(self):
        # Auto-build if needed
        if self.dfa is None:
            if not self.canvas.states:
                self.status_var.set('No hay automata definido')
                return
            self.dfa = self._build_dfa_from_canvas()

        if self.dfa.initial_state is None:
            self.status_var.set('No hay estado inicial definido')
            self._clear_results()
            self._write_result('Error: No hay estado inicial definido.\n', 'error')
            return

        input_str = self.test_entry.get()
        self._clear_results()
        accepted, path, msg = self.dfa.test(input_str)

        display_str = input_str if input_str else '\u03b5 (cadena vacia)'
        self._write_result(f'Probando: "{display_str}"\n\n', 'info')

        if path:
            self._write_result('Camino: ', 'step')
            path_strs = []
            for i, (state, symbol) in enumerate(path):
                if i == 0:
                    path_strs.append(f'[{state}]')
                else:
                    path_strs.append(f'--{symbol}--> [{state}]')
            self._write_result(' '.join(path_strs) + '\n\n')

        tag = 'accepted' if accepted else 'rejected'
        self._write_result(f'Resultado: {msg}\n', tag)

        # Highlight final state on canvas
        if path:
            final_state = path[-1][0]
            hl_type = 'accept' if accepted else 'reject'
            self.canvas.highlight_states({final_state}, hl_type)

    def _on_step(self):
        """Step-by-step simulation."""
        # Auto-build if needed
        if self.dfa is None:
            if not self.canvas.states:
                self.status_var.set('No hay automata definido')
                return
            self.dfa = self._build_dfa_from_canvas()

        if self.dfa.initial_state is None:
            self.status_var.set('No hay estado inicial definido')
            return

        input_str = self.test_entry.get()

        # Initialize or reset stepping
        if self._step_string != input_str or self._step_index >= len(input_str) + 1:
            self._step_string = input_str
            self._step_index = 0
            accepted, path, msg = self.dfa.test(input_str)
            self._step_path = path
            self._clear_results()
            display_str = input_str if input_str else '\u03b5'
            self._write_result(f'Simulacion paso a paso: "{display_str}"\n', 'info')
            self._write_result(f'{"=" * 40}\n\n')

        if self._step_index < len(self._step_path):
            state, symbol = self._step_path[self._step_index]

            if self._step_index == 0:
                self._write_result(f'Paso 0: Estado inicial = [{state}]\n', 'step')
                remaining = input_str
                self._write_result(f'  Cadena restante: "{remaining}"\n\n')
            else:
                self._write_result(
                    f'Paso {self._step_index}: Lee \'{symbol}\' -> [{state}]\n', 'step')
                remaining = input_str[self._step_index:]
                self._write_result(f'  Cadena restante: "{remaining}"\n\n')

            # Highlight current state
            hl_type = 'normal'
            if self._step_index == len(self._step_path) - 1:
                hl_type = 'accept' if state in self.dfa.accept_states else 'reject'
            self.canvas.highlight_states({state}, hl_type)

            self._step_index += 1

            if self._step_index >= len(self._step_path):
                accepted = state in self.dfa.accept_states
                tag = 'accepted' if accepted else 'rejected'
                msg = 'ACEPTADA' if accepted else 'RECHAZADA'
                self._write_result(f'\nResultado final: {msg}\n', tag)
                self.status_var.set(f'Simulacion completada - {msg}')
        else:
            # Already finished, reset
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
