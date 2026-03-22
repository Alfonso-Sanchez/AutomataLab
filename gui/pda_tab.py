"""PDA interactive editor tab."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from gui.canvas_renderer import AutomataCanvas
from core.pda import PDA


class PDATransitionDialog(tk.Toplevel):
    """Custom dialog for PDA transition input with three fields."""

    def __init__(self, parent, from_state, to_state):
        super().__init__(parent)
        self.title('Transicion PDA')
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(False, False)

        self.result = None

        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f'Transicion: {from_state} \u2192 {to_state}',
                  font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=3,
                                                       sticky=tk.W, pady=(0, 10))

        ttk.Label(main, text='Simbolo de entrada:').grid(
            row=1, column=0, sticky=tk.W, pady=2)
        self.input_var = ttk.Entry(main, font=('Consolas', 11), width=15)
        self.input_var.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Button(main, text='\u03b5', width=2,
                   command=lambda: self._insert_epsilon(self.input_var)
                   ).grid(row=1, column=2, padx=(3, 0), pady=2)

        ttk.Label(main, text='Tope de pila:').grid(
            row=2, column=0, sticky=tk.W, pady=2)
        self.stack_top_var = ttk.Entry(main, font=('Consolas', 11), width=15)
        self.stack_top_var.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Button(main, text='\u03b5', width=2,
                   command=lambda: self._insert_epsilon(self.stack_top_var)
                   ).grid(row=2, column=2, padx=(3, 0), pady=2)

        ttk.Label(main, text='Push en pila:').grid(
            row=3, column=0, sticky=tk.W, pady=2)
        self.stack_push_var = ttk.Entry(main, font=('Consolas', 11), width=15)
        self.stack_push_var.grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Button(main, text='\u03b5', width=2,
                   command=lambda: self._insert_epsilon(self.stack_push_var)
                   ).grid(row=3, column=2, padx=(3, 0), pady=2)

        ttk.Label(main, text='Formato resultado: entrada, tope/push',
                  font=('Segoe UI', 8, 'italic'),
                  foreground='#888888').grid(row=4, column=0, columnspan=3,
                                             sticky=tk.W, pady=(8, 0))

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(12, 0))

        ttk.Button(btn_frame, text='Aceptar', command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Cancelar', command=self._on_cancel).pack(side=tk.LEFT, padx=5)

        self.input_var.focus_set()
        self.bind('<Return>', lambda e: self._on_ok())
        self.bind('<Escape>', lambda e: self._on_cancel())

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_toplevel()
        x = pw.winfo_x() + (pw.winfo_width() - self.winfo_width()) // 2
        y = pw.winfo_y() + (pw.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')

    def _insert_epsilon(self, entry):
        """Insert ε at cursor position in the given entry."""
        entry.insert(tk.INSERT, '\u03b5')
        entry.focus_set()

    def _on_ok(self):
        inp = self.input_var.get().strip()
        top = self.stack_top_var.get().strip()
        push = self.stack_push_var.get().strip()

        if not top:
            messagebox.showwarning('Campo requerido',
                                   'El tope de pila es requerido.',
                                   parent=self)
            return

        # Normalize epsilon
        if inp.lower() in ('eps', 'epsilon', '', 'e'):
            inp = '\u03b5'
        if push.lower() in ('eps', 'epsilon', '', 'e'):
            push = '\u03b5'
        if not push:
            push = '\u03b5'
        if not inp:
            inp = '\u03b5'

        # Format: "input, top/push"
        self.result = f'{inp}, {top}/{push}'
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class PDATab(ttk.Frame):
    """Interactive PDA builder and tester tab."""

    def __init__(self, parent):
        super().__init__(parent)
        self.pda = None
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
        self.canvas.automaton_type = 'PDA'
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.set_transition_dialog(self._transition_dialog)
        self.canvas.set_on_change(self._on_canvas_change)

        # Row 1: Examples + Import/Export
        extra_bar1 = ttk.Frame(left_frame)
        extra_bar1.pack(fill=tk.X, pady=(2, 0))

        ttk.Label(extra_bar1, text='Ejemplo:').pack(side=tk.LEFT, padx=(0, 2))
        self._example_var = tk.StringVar(value='Seleccionar...')
        example_combo = ttk.Combobox(extra_bar1, textvariable=self._example_var,
                                     values=['a^n b^n', 'Palindromos pares'],
                                     state='readonly', width=18)
        example_combo.pack(side=tk.LEFT, padx=2)
        example_combo.bind('<<ComboboxSelected>>', self._on_example_selected)

        ttk.Button(extra_bar1, text='Importar',
                   command=self._on_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(extra_bar1, text='Exportar',
                   command=self._on_export).pack(side=tk.RIGHT, padx=2)

        # Row 2: PDA-specific settings
        extra_bar2 = ttk.Frame(left_frame)
        extra_bar2.pack(fill=tk.X, pady=(2, 0))

        ttk.Label(extra_bar2, text='Aceptar por:').pack(side=tk.LEFT, padx=(0, 2))
        self._accept_mode_var = tk.StringVar(value='Estado final')
        accept_combo = ttk.Combobox(extra_bar2, textvariable=self._accept_mode_var,
                                    values=['Estado final', 'Pila vacia'],
                                    state='readonly', width=14)
        accept_combo.pack(side=tk.LEFT, padx=2)

        ttk.Label(extra_bar2, text='Pila inicial:').pack(side=tk.LEFT, padx=(6, 2))
        self._stack_symbol_var = tk.StringVar(value='Z')
        stack_entry = ttk.Entry(extra_bar2, textvariable=self._stack_symbol_var,
                                font=('Consolas', 10), width=3)
        stack_entry.pack(side=tk.LEFT, padx=2)

        # --- Right panel: Testing ---
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text='Probar Cadenas',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=(5, 2))

        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(input_frame, text='Cadena:').pack(side=tk.LEFT)
        self.test_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.test_entry.bind('<Return>', lambda e: self._on_test())

        ttk.Button(input_frame, text='Probar',
                   command=self._on_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_frame, text='Traza',
                   command=self._on_step).pack(side=tk.LEFT, padx=2)

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

        self.status_var = tk.StringVar(value='Listo. Agrega estados con la barra de herramientas.')
        ttk.Label(self, textvariable=self.status_var,
                  relief=tk.SUNKEN, anchor=tk.W,
                  font=('Segoe UI', 9)).pack(fill=tk.X, side=tk.BOTTOM)

    # ──────────────────────────────────────────────
    # Transition dialog (PDA-specific: 3 fields)
    # ──────────────────────────────────────────────

    def _transition_dialog(self, from_state, to_state):
        """Open custom 3-field dialog for PDA transitions."""
        dlg = PDATransitionDialog(self, from_state, to_state)
        self.wait_window(dlg)
        return dlg.result

    # ──────────────────────────────────────────────
    # Canvas change
    # ──────────────────────────────────────────────

    def _on_canvas_change(self):
        n_states = len(self.canvas.states)
        n_trans = len(self.canvas.transitions)
        self.status_var.set(f'PDA: {n_states} estados, {n_trans} transiciones')
        self.pda = None

    # ──────────────────────────────────────────────
    # Build PDA from canvas
    # ──────────────────────────────────────────────

    def _parse_pda_label(self, label):
        """Parse label like 'a, Z/AZ' into (input_sym, stack_top, stack_push)."""
        try:
            # Format: "input, top/push"
            parts = label.split(',', 1)
            if len(parts) != 2:
                return None
            input_sym = parts[0].strip()
            rest = parts[1].strip()
            if '/' not in rest:
                return None
            top_push = rest.split('/', 1)
            stack_top = top_push[0].strip()
            stack_push = top_push[1].strip()
            return (input_sym, stack_top, stack_push)
        except Exception:
            return None

    def _build_pda_from_canvas(self):
        pda = PDA()
        pda.states = list(self.canvas.states.keys())
        for name, data in self.canvas.states.items():
            if data['is_initial']:
                pda.initial_state = name
            if data['is_accept']:
                pda.accept_states.add(name)

        pda.initial_stack_symbol = self._stack_symbol_var.get().strip() or 'Z'

        if self._accept_mode_var.get() == 'Pila vacia':
            pda.accept_by = 'empty_stack'
        else:
            pda.accept_by = 'state'

        for t in self.canvas.transitions:
            parsed = self._parse_pda_label(t['label'])
            if parsed is None:
                continue
            input_sym, stack_top, stack_push = parsed
            # Normalize epsilon
            if input_sym.lower() in ('eps', 'epsilon'):
                input_sym = '\u03b5'
            if stack_push.lower() in ('eps', 'epsilon'):
                stack_push = '\u03b5'

            key = (t['from'], input_sym, stack_top)
            if key not in pda.transitions:
                pda.transitions[key] = []
            pda.transitions[key].append((t['to'], stack_push))

            if input_sym != '\u03b5' and input_sym not in pda.input_alphabet:
                pda.input_alphabet.append(input_sym)
            if stack_top not in pda.stack_alphabet:
                pda.stack_alphabet.append(stack_top)
            if stack_push != '\u03b5':
                for ch in stack_push:
                    if ch not in pda.stack_alphabet:
                        pda.stack_alphabet.append(ch)

        return pda

    def _on_build(self):
        if not self.canvas.states:
            self.status_var.set('No hay estados definidos')
            return
        pda = self._build_pda_from_canvas()
        if pda.initial_state is None:
            self.status_var.set('Error: No hay estado inicial definido')
            self._clear_results()
            self._write_result('No hay estado inicial. Usa el modo "Inicial" para asignar uno.\n', 'error')
            return
        self.pda = pda
        total_trans = sum(len(v) for v in pda.transitions.values())
        self.status_var.set(
            f'PDA construido: {len(pda.states)} estados, '
            f'{total_trans} transiciones, '
            f'aceptacion por {"pila vacia" if pda.accept_by == "empty_stack" else "estado final"}'
        )
        self._clear_results()
        self._write_result('PDA construido exitosamente.\n', 'info')
        self._write_result(f'  Estados: {", ".join(pda.states)}\n')
        self._write_result(f'  Inicial: {pda.initial_state}\n')
        self._write_result(f'  Simbolo pila inicial: {pda.initial_stack_symbol}\n')
        self._write_result(f'  Aceptacion: {", ".join(pda.accept_states) if pda.accept_states else "pila vacia"}\n')
        self._write_result(f'  Modo: {"Pila vacia" if pda.accept_by == "empty_stack" else "Estado final"}\n')

    # ──────────────────────────────────────────────
    # Examples
    # ──────────────────────────────────────────────

    def _on_example_selected(self, event=None):
        choice = self._example_var.get()
        if 'a^n' in choice.lower() or 'b^n' in choice.lower():
            text = PDA.example()
        else:
            text = PDA.example2()
        pda, errors = PDA.parse(text)
        if pda and not errors:
            labels = pda.get_transition_labels()
            self.canvas.load_from_model(pda.states, pda.initial_state,
                                        pda.accept_states, labels)
            self.pda = pda
            # Sync UI controls
            self._stack_symbol_var.set(pda.initial_stack_symbol)
            if pda.accept_by == 'empty_stack':
                self._accept_mode_var.set('Pila vacia')
            else:
                self._accept_mode_var.set('Estado final')
            self.status_var.set(f'Ejemplo cargado: {len(pda.states)} estados')
            self._clear_results()
            self._write_result('Ejemplo cargado en el canvas.\n', 'info')

    # ──────────────────────────────────────────────
    # Import / Export
    # ──────────────────────────────────────────────

    def _on_import(self):
        win = tk.Toplevel(self)
        win.title('Importar PDA desde texto')
        win.geometry('650x500')
        win.minsize(550, 400)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Pega la definicion del PDA:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def do_import():
            text = editor.get('1.0', tk.END)
            pda, errors = PDA.parse(text)
            if errors:
                messagebox.showerror('Errores de parseo', '\n'.join(errors), parent=win)
                return
            labels = pda.get_transition_labels()
            self.canvas.load_from_model(pda.states, pda.initial_state,
                                        pda.accept_states, labels)
            self.pda = pda
            self._stack_symbol_var.set(pda.initial_stack_symbol)
            if pda.accept_by == 'empty_stack':
                self._accept_mode_var.set('Pila vacia')
            else:
                self._accept_mode_var.set('Estado final')
            self.status_var.set(f'PDA importado: {len(pda.states)} estados')
            self._clear_results()
            self._write_result('PDA importado exitosamente desde texto.\n', 'info')
            win.destroy()

        ttk.Button(btn_frame, text='Importar', command=do_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cancelar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_export(self):
        if not self.canvas.states:
            messagebox.showinfo('Exportar', 'No hay automata para exportar.', parent=self)
            return

        pda = self._build_pda_from_canvas()
        lines = []
        lines.append(f'States: {", ".join(pda.states)}')
        lines.append(f'Input Alphabet: {", ".join(pda.input_alphabet)}')
        lines.append(f'Stack Alphabet: {", ".join(pda.stack_alphabet)}')
        lines.append(f'Initial: {pda.initial_state or ""}')
        lines.append(f'Initial Stack: {pda.initial_stack_symbol}')
        if pda.accept_by == 'empty_stack':
            lines.append('Accept by: empty stack')
        else:
            lines.append(f'Accept: {", ".join(sorted(pda.accept_states))}')
        lines.append('Transitions:')
        for (from_s, input_sym, stack_top), targets in sorted(pda.transitions.items()):
            for to_s, stack_push in targets:
                lines.append(f'{from_s}, {input_sym}, {stack_top} -> {to_s}, {stack_push}')
        text = '\n'.join(lines)

        win = tk.Toplevel(self)
        win.title('Exportar PDA como texto')
        win.geometry('650x450')
        win.minsize(550, 350)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Definicion del PDA:',
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
        if self.pda is None:
            if not self.canvas.states:
                self.status_var.set('No hay automata definido')
                return
            self.pda = self._build_pda_from_canvas()

        if self.pda.initial_state is None:
            self.status_var.set('No hay estado inicial definido')
            self._clear_results()
            self._write_result('Error: No hay estado inicial definido.\n', 'error')
            return

        input_str = self.test_entry.get()
        self._clear_results()
        accepted, trace, msg = self.pda.test(input_str)

        display_str = input_str if input_str else '\u03b5 (cadena vacia)'
        self._write_result(f'Probando: "{display_str}"\n\n', 'info')

        if trace:
            self._write_result('Traza de ejecucion:\n', 'step')
            self._write_result(f'  {"Estado":<10} {"Entrada restante":<20} {"Pila"}\n')
            self._write_result(f'  {"-" * 50}\n')
            for state, remaining, stack in trace:
                rem = remaining if remaining else '\u03b5'
                self._write_result(f'  {state:<10} {rem:<20} {stack}\n')
            self._write_result('\n')

        tag = 'accepted' if accepted else 'rejected'
        self._write_result(f'Resultado: {msg}\n', tag)

        if trace:
            final_state = trace[-1][0]
            hl_type = 'accept' if accepted else 'reject'
            self.canvas.highlight_states({final_state}, hl_type)

    def _on_step(self):
        """For PDA, step-by-step shows full trace (same as test, due to BFS nature)."""
        self._on_test()

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
