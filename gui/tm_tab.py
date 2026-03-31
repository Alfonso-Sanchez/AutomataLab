"""Turing Machine interactive editor tab."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from gui.canvas_renderer import AutomataCanvas
from core.tm import TuringMachine, BLANK


class TMTransitionDialog(tk.Toplevel):
    """Custom dialog for TM transition input: read -> write, direction."""

    def __init__(self, parent, from_state, to_state):
        super().__init__(parent)
        self.title('Transicion TM')
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(False, False)

        self.result = None

        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f'Transicion: {from_state} \u2192 {to_state}',
                  font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=4,
                                                       sticky=tk.W, pady=(0, 10))

        # Read symbol
        ttk.Label(main, text='Leer (simbolo en cinta):').grid(
            row=1, column=0, sticky=tk.W, pady=2)
        self.read_entry = ttk.Entry(main, font=('Consolas', 11), width=10)
        self.read_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Button(main, text='\u2294', width=2,
                   command=lambda: self._insert_sym(self.read_entry, BLANK)
                   ).grid(row=1, column=2, padx=(3, 0), pady=2)

        # Write symbol
        ttk.Label(main, text='Escribir:').grid(
            row=2, column=0, sticky=tk.W, pady=2)
        self.write_entry = ttk.Entry(main, font=('Consolas', 11), width=10)
        self.write_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Button(main, text='\u2294', width=2,
                   command=lambda: self._insert_sym(self.write_entry, BLANK)
                   ).grid(row=2, column=2, padx=(3, 0), pady=2)

        # Direction
        ttk.Label(main, text='Mover cabezal:').grid(
            row=3, column=0, sticky=tk.W, pady=2)
        self.dir_var = tk.StringVar(value='R')
        dir_frame = ttk.Frame(main)
        dir_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Radiobutton(dir_frame, text='R (Derecha)', variable=self.dir_var,
                         value='R').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(dir_frame, text='L (Izquierda)', variable=self.dir_var,
                         value='L').pack(side=tk.LEFT)

        # Format hint
        ttk.Label(main, text='Formato: leer \u2192 escribir, direccion',
                  font=('Segoe UI', 8, 'italic'),
                  foreground='#888888').grid(row=4, column=0, columnspan=4,
                                             sticky=tk.W, pady=(8, 0))

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=5, column=0, columnspan=4, pady=(12, 0))
        ttk.Button(btn_frame, text='Aceptar', command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Cancelar', command=self._on_cancel).pack(side=tk.LEFT, padx=5)

        self.read_entry.focus_set()
        self.bind('<Return>', lambda e: self._on_ok())
        self.bind('<Escape>', lambda e: self._on_cancel())

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_toplevel()
        x = pw.winfo_x() + (pw.winfo_width() - self.winfo_width()) // 2
        y = pw.winfo_y() + (pw.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')

    def _insert_sym(self, entry, sym):
        entry.delete(0, tk.END)
        entry.insert(0, sym)
        entry.focus_set()

    def _on_ok(self):
        read_sym = self.read_entry.get().strip()
        write_sym = self.write_entry.get().strip()
        direction = self.dir_var.get()

        if not read_sym:
            messagebox.showwarning('Campo requerido',
                                   'El simbolo a leer es requerido.', parent=self)
            return
        if not write_sym:
            write_sym = read_sym  # Default: no change

        # Normalize blank
        if read_sym in ('_', 'B', 'blank'):
            read_sym = BLANK
        if write_sym in ('_', 'B', 'blank'):
            write_sym = BLANK

        # Format: "read→write,D"
        self.result = f'{read_sym}\u2192{write_sym},{direction}'
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class TMTab(ttk.Frame):
    """Interactive Turing Machine builder and tester tab."""

    def __init__(self, parent):
        super().__init__(parent)
        self.tm = None
        self._step_gen = None
        self._step_active = False
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
        self.canvas.automaton_type = 'TM'
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.set_transition_dialog(self._transition_dialog)
        self.canvas.set_on_change(self._on_canvas_change)

        # Extra bar: Examples + Import/Export
        extra_bar = ttk.Frame(left_frame)
        extra_bar.pack(fill=tk.X, pady=(2, 0))

        ttk.Label(extra_bar, text='Ejemplo:').pack(side=tk.LEFT, padx=(0, 2))
        self._example_var = tk.StringVar(value='Seleccionar...')
        example_combo = ttk.Combobox(extra_bar, textvariable=self._example_var,
                                     values=['0^(2^n)', 'w#w'],
                                     state='readonly', width=18)
        example_combo.pack(side=tk.LEFT, padx=2)
        example_combo.bind('<<ComboboxSelected>>', self._on_example_selected)

        ttk.Button(extra_bar, text='Importar',
                   command=self._on_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(extra_bar, text='Exportar',
                   command=self._on_export).pack(side=tk.RIGHT, padx=2)

        # TM-specific mode buttons (accept / reject assignment)
        settings_bar = ttk.Frame(left_frame)
        settings_bar.pack(fill=tk.X, pady=(2, 0))

        self._accept_var = tk.StringVar(value='—')
        self._reject_var = tk.StringVar(value='—')

        # "Aceptar" shortcut: activates the canvas's existing set_accept mode
        ttk.Button(settings_bar, text='\u2713 Aceptar',
                   command=lambda: self.canvas.set_mode('set_accept')
                   ).pack(side=tk.LEFT, padx=(0, 2))

        self._accept_label = ttk.Label(settings_bar, textvariable=self._accept_var,
                                       font=('Consolas', 9), foreground='#2E7D32', width=12)
        self._accept_label.pack(side=tk.LEFT, padx=(0, 8))

        # "Rechazar" shortcut: activates the new set_reject mode
        btn_reject = ttk.Button(settings_bar, text='\u2717 Rechazar',
                                command=lambda: self.canvas.set_mode('set_reject'))
        btn_reject.pack(side=tk.LEFT, padx=(0, 2))
        # Register so canvas toolbar highlights it when active
        self.canvas.register_mode_button('set_reject', btn_reject)

        self._reject_label = ttk.Label(settings_bar, textvariable=self._reject_var,
                                       font=('Consolas', 9), foreground='#C62828', width=12)
        self._reject_label.pack(side=tk.LEFT)

        # --- Right panel: Tape + Testing + Info ---
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)

        # Right notebook for multiple views
        self._right_notebook = ttk.Notebook(right_frame)
        self._right_notebook.pack(fill=tk.BOTH, expand=True)

        # === Tab 1: Ejecucion ===
        exec_frame = ttk.Frame(self._right_notebook)
        self._right_notebook.add(exec_frame, text='Ejecucion')

        # Input row
        input_frame = ttk.Frame(exec_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=(5, 2))

        ttk.Label(input_frame, text='Cadena:').pack(side=tk.LEFT)
        self.test_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.test_entry.bind('<Return>', lambda e: self._on_test())

        ttk.Button(input_frame, text='Ejecutar',
                   command=self._on_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_frame, text='Paso a paso',
                   command=self._on_step_start).pack(side=tk.LEFT, padx=2)

        # Step controls
        self._step_frame = ttk.Frame(exec_frame)
        self._step_frame.pack(fill=tk.X, padx=5, pady=2)
        self._btn_next = ttk.Button(self._step_frame, text='Siguiente',
                                     command=self._on_step_next)
        self._btn_next.pack(side=tk.LEFT, padx=2)
        self._step_label = ttk.Label(self._step_frame, text='',
                                      font=('Segoe UI', 9, 'italic'))
        self._step_label.pack(side=tk.LEFT, padx=10)
        self._step_frame.pack_forget()

        # Tape visualizer
        tape_frame = ttk.LabelFrame(exec_frame, text='Cinta')
        tape_frame.pack(fill=tk.X, padx=5, pady=(2, 0))

        self._tape_canvas = tk.Canvas(tape_frame, height=70, bg='#FAFAFA',
                                       highlightthickness=0)
        self._tape_canvas.pack(fill=tk.X, padx=3, pady=3)

        # Results
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
        self.results.tag_configure('config', foreground='#80CBC4',
                                   font=('Consolas', 10))
        self.results.tag_configure('loop', foreground='#FFB74D',
                                   font=('Consolas', 10, 'bold'))

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
        self._info_text.tag_configure('reject_st', foreground='#F44336',
                                       font=('Consolas', 10, 'bold'))


        self.status_var = tk.StringVar(value='Listo. Crea una Maquina de Turing.')
        ttk.Label(self, textvariable=self.status_var,
                  relief=tk.SUNKEN, anchor=tk.W,
                  font=('Segoe UI', 9)).pack(fill=tk.X, side=tk.BOTTOM)

    # ──────────────────────────────────────────────
    # Tape visualization
    # ──────────────────────────────────────────────

    def _draw_tape(self, tape, head, state=''):
        """Draw the tape with head indicator."""
        c = self._tape_canvas
        c.delete('all')
        c.update_idletasks()
        w = c.winfo_width()
        h = c.winfo_height()

        cell_w = 32
        cell_h = 32

        # Show a window of cells centered on head
        visible = max(w // cell_w, 10)
        start_idx = max(0, head - visible // 2)
        end_idx = min(len(tape), start_idx + visible)
        # Pad with blanks
        while end_idx - start_idx < visible:
            end_idx += 1

        total_cells = end_idx - start_idx
        start_x = max(5, (w - total_cells * cell_w) // 2)
        y = 8

        # State label
        if state:
            c.create_text(w // 2, y + cell_h + 22, text=f'Estado: {state}',
                           font=('Consolas', 9, 'bold'), fill='#333')

        for i in range(total_cells):
            idx = start_idx + i
            sym = tape[idx] if idx < len(tape) else BLANK
            x = start_x + i * cell_w

            is_head = (idx == head)
            fill = '#FFF9C4' if is_head else '#F5F5F5'
            border = '#F57F17' if is_head else '#BDBDBD'
            bw = 2 if is_head else 1

            c.create_rectangle(x, y, x + cell_w, y + cell_h,
                               fill=fill, outline=border, width=bw)
            c.create_text(x + cell_w // 2, y + cell_h // 2, text=sym,
                           font=('Consolas', 13, 'bold' if is_head else 'normal'),
                           fill='#F57F17' if is_head else '#333')

            # Head arrow
            if is_head:
                arrow_y = y + cell_h + 3
                cx = x + cell_w // 2
                c.create_polygon(cx - 6, arrow_y + 10, cx + 6, arrow_y + 10,
                                 cx, arrow_y,
                                 fill='#F57F17', outline='#E65100')

    # ──────────────────────────────────────────────
    # Transition dialog
    # ──────────────────────────────────────────────

    def _transition_dialog(self, from_state, to_state):
        dlg = TMTransitionDialog(self, from_state, to_state)
        self.wait_window(dlg)
        return dlg.result

    def _on_canvas_change(self):
        n_states = len(self.canvas.states)
        n_trans = len(self.canvas.transitions)
        self.status_var.set(f'TM: {n_states} estados, {n_trans} transiciones')
        self.tm = None
        # Sync accept/reject labels from canvas
        accept_name = next((n for n, d in self.canvas.states.items() if d['is_accept']), None)
        reject_name = next(iter(self.canvas.reject_states), None) if self.canvas.reject_states else None
        self._accept_var.set(accept_name or '—')
        self._reject_var.set(reject_name or '—')
        self._update_info_tab()

    # ──────────────────────────────────────────────
    # Build TM from canvas
    # ──────────────────────────────────────────────

    def _parse_tm_label(self, label):
        """Parse label like 'a→b,R' into (read, write, direction)."""
        try:
            if '\u2192' in label:
                read_sym, rest = label.split('\u2192', 1)
            elif '->' in label:
                read_sym, rest = label.split('->', 1)
            else:
                return None
            parts = [p.strip() for p in rest.split(',')]
            if len(parts) != 2:
                return None
            write_sym = parts[0].strip()
            direction = parts[1].strip().upper()
            if direction not in ('L', 'R'):
                return None
            return (read_sym.strip(), write_sym, direction)
        except Exception:
            return None

    def _build_tm_from_canvas(self):
        tm = TuringMachine()
        tm.states = list(self.canvas.states.keys())
        # Read accept/reject directly from canvas visual state
        tm.accept_state = next((n for n, d in self.canvas.states.items() if d['is_accept']), None)
        tm.reject_state = next(iter(self.canvas.reject_states), None) if self.canvas.reject_states else None

        for name, data in self.canvas.states.items():
            if data['is_initial']:
                tm.initial_state = name

        for t in self.canvas.transitions:
            for sub_label in t['label'].split('\n'):
                parsed = self._parse_tm_label(sub_label.strip())
                if parsed is None:
                    continue
                read_sym, write_sym, direction = parsed
                key = (t['from'], read_sym)
                tm.transitions[key] = (t['to'], write_sym, direction)

                if read_sym != BLANK and read_sym not in tm.input_alphabet:
                    tm.input_alphabet.append(read_sym)
                for s in (read_sym, write_sym):
                    if s not in tm.tape_alphabet:
                        tm.tape_alphabet.append(s)

        if BLANK not in tm.tape_alphabet:
            tm.tape_alphabet.append(BLANK)

        return tm

    # ──────────────────────────────────────────────
    # Test
    # ──────────────────────────────────────────────

    def _on_test(self):
        self._step_frame.pack_forget()
        self._step_active = False

        if self.tm is None:
            if not self.canvas.states:
                self.status_var.set('No hay automata definido')
                return
            self.tm = self._build_tm_from_canvas()

        if self.tm.initial_state is None:
            self.status_var.set('No hay estado inicial')
            self._clear_results()
            self._write_result('Error: No hay estado inicial.\n', 'error')
            return

        input_str = self.test_entry.get()
        self._clear_results()
        result, trace, msg = self.tm.test(input_str)

        display_str = input_str if input_str else '\u03b5 (cadena vacia)'
        self._write_result(f'Ejecutando TM con entrada: "{display_str}"\n\n', 'info')

        # Show using textbook configuration notation
        if trace:
            total_steps = trace[-1][3]
            self._write_result(f'Pasos ejecutados: {total_steps}\n', 'step')
            self._write_result('Configuraciones (notacion del libro):\n\n', 'info')

            show_count = min(30, len(trace))
            if len(trace) > show_count:
                self._write_result(f'  (mostrando ultimos {show_count} de {len(trace)})\n\n')
                start = len(trace) - show_count
            else:
                start = 0

            for i in range(start, len(trace)):
                state, tape, head, step = trace[i]
                config = TuringMachine.configuration_string(state, tape, head)
                prefix = '\u22a2 ' if i > start else '  '
                self._write_result(f'  {prefix}', 'step')
                self._write_result(f'{config}\n', 'config')

            # Draw final tape state
            final_state, final_tape, final_head, _ = trace[-1]
            self._draw_tape(final_tape, final_head, final_state)
            self._write_result('\n')

        tag = {'accept': 'accepted', 'reject': 'rejected', 'loop': 'loop'}.get(result, 'error')
        self._write_result(f'Resultado: {msg}\n', tag)

        # Update info tab
        self._update_info_tab()

        if trace:
            final_state = trace[-1][0]
            hl_type = 'accept' if result == 'accept' else 'reject'
            self.canvas.highlight_states({final_state}, hl_type)

    # ──────────────────────────────────────────────
    # Step-by-step
    # ──────────────────────────────────────────────

    def _on_step_start(self):
        if self.tm is None:
            if not self.canvas.states:
                self.status_var.set('No hay automata definido')
                return
            self.tm = self._build_tm_from_canvas()

        if self.tm.initial_state is None:
            self.status_var.set('No hay estado inicial')
            return

        input_str = self.test_entry.get()
        self._clear_results()

        self._step_gen = self.tm.step_generator(input_str)
        self._step_active = True
        self._btn_next.config(state='normal')

        display_str = input_str if input_str else '\u03b5'
        self._write_result(f'Simulacion paso a paso: "{display_str}"\n', 'info')
        self._write_result('Configuraciones (notacion del libro):\n', 'info')
        self._write_result(f'{"=" * 50}\n\n')

        self._step_frame.pack(fill=tk.X, padx=5, pady=2,
                               before=self._tape_canvas.master)

        # Update info tab
        self._update_info_tab()

        # Show first step
        self._on_step_next()

    def _on_step_next(self):
        if not self._step_active or self._step_gen is None:
            return

        try:
            state, tape, head, step, status = next(self._step_gen)
        except StopIteration:
            self._step_active = False
            self._btn_next.config(state='disabled')
            return

        # Configuration notation: w1...w_{i-1} q w_i...w_n
        config = TuringMachine.configuration_string(state, tape, head)
        prefix = '\u22a2 ' if step > 0 else '  '
        self._write_result(f'{prefix}', 'step')
        self._write_result(f'{config}\n', 'config')

        self._draw_tape(tape, head, state)
        self._step_label.config(text=f'Paso {step}  Estado: {state}')

        # Highlight state
        hl_type = 'normal'
        if status == 'accept':
            hl_type = 'accept'
        elif status in ('reject', 'loop'):
            hl_type = 'reject'
        self.canvas.highlight_states({state}, hl_type)

        if status != 'running':
            self._step_active = False
            self._btn_next.config(state='disabled')
            msg_map = {'accept': 'ACEPTADA', 'reject': 'RECHAZADA',
                       'loop': 'BUCLE DETECTADO'}
            tag_map = {'accept': 'accepted', 'reject': 'rejected', 'loop': 'loop'}
            self._write_result(f'\nResultado: {msg_map.get(status, status)}\n',
                               tag_map.get(status, 'error'))

    # ──────────────────────────────────────────────
    # Info tab: Formal definition + Transition table
    # ──────────────────────────────────────────────

    def _update_info_tab(self):
        """Update the formal definition and transition table tab."""
        if not self.canvas.states:
            t = self._info_text
            t.config(state='normal')
            t.delete('1.0', tk.END)
            t.insert(tk.END, '(Agrega estados al canvas para ver la definicion formal)\n')
            t.config(state='disabled')
            return

        tm = self.tm if self.tm is not None else self._build_tm_from_canvas()

        t = self._info_text
        t.config(state='normal')
        t.delete('1.0', tk.END)

        # 7-tuple formal definition
        t.insert(tk.END, 'DEFINICION FORMAL (7-tupla)\n', 'title')
        t.insert(tk.END, '=' * 40 + '\n\n')
        t.insert(tk.END, tm.get_formal_definition() + '\n\n', 'formal')

        # Special states
        t.insert(tk.END, 'Estados especiales:\n', 'header')
        t.insert(tk.END, f'  q_accept = {tm.accept_state or "—"}', 'accept_st')
        t.insert(tk.END, '  (acepta inmediatamente)\n')
        t.insert(tk.END, f'  q_reject = {tm.reject_state or "—"}', 'reject_st')
        t.insert(tk.END, '  (rechaza inmediatamente)\n\n')

        # Transition table
        t.insert(tk.END, 'TABLA DE TRANSICION \u03b4\n', 'title')
        t.insert(tk.END, '=' * 40 + '\n\n')

        rows = tm.get_transition_table()
        if rows:
            t.insert(tk.END,
                     f'  {"Estado":<12} {"Lee":<6} {"Nuevo":<12} {"Escribe":<8} {"Dir"}\n',
                     'header')
            t.insert(tk.END, f'  {"-" * 48}\n')

            for from_s, read_s, to_s, write_s, d in rows:
                line = f'  {from_s:<12} {read_s:<6} {to_s:<12} {write_s:<8} {d}\n'
                if to_s == tm.accept_state:
                    t.insert(tk.END, line, 'accept_st')
                elif to_s == tm.reject_state:
                    t.insert(tk.END, line, 'reject_st')
                else:
                    t.insert(tk.END, line)

            t.insert(tk.END, f'\n  Total: {len(rows)} transiciones\n')

            t.insert(tk.END, '\nNOTACION FORMAL:\n', 'title')
            t.insert(tk.END, '=' * 40 + '\n\n')
            for from_s, read_s, to_s, write_s, d in rows:
                t.insert(tk.END,
                         f'  \u03b4({from_s}, {read_s}) = ({to_s}, {write_s}, {d})\n',
                         'formal')

        t.config(state='disabled')

    # ──────────────────────────────────────────────
    # Examples
    # ──────────────────────────────────────────────

    def _on_example_selected(self, event=None):
        choice = self._example_var.get()
        if 'w#w' in choice:
            text = TuringMachine.example2()
        else:
            text = TuringMachine.example()
        tm, errors = TuringMachine.parse(text)
        if tm and not errors:
            labels = tm.get_transition_labels()
            # Mark accept and reject states
            accept_states = set()
            if tm.accept_state and tm.accept_state in tm.states:
                accept_states.add(tm.accept_state)
            self.canvas.reject_states = {tm.reject_state} if tm.reject_state else set()
            self.canvas.load_from_model(tm.states, tm.initial_state,
                                        accept_states, labels)
            self.tm = tm
            self._accept_var.set(tm.accept_state or '')
            self._reject_var.set(tm.reject_state or '')
            self.status_var.set(f'Ejemplo cargado: {len(tm.states)} estados')
            self._clear_results()
            self._write_result('Ejemplo cargado.\n', 'info')
            self._write_result(f'  q_accept = {tm.accept_state}  (doble circulo verde)\n', 'accepted')
            self._write_result(f'  q_reject = {tm.reject_state}  (X rojo)\n', 'rejected')
            self._update_info_tab()

    # ──────────────────────────────────────────────
    # Import / Export
    # ──────────────────────────────────────────────

    def _on_import(self):
        win = tk.Toplevel(self)
        win.title('Importar TM desde texto')
        win.geometry('650x500')
        win.minsize(550, 400)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Pega la definicion de la Maquina de Turing:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def do_import():
            text = editor.get('1.0', tk.END)
            tm, errors = TuringMachine.parse(text)
            if errors:
                messagebox.showerror('Errores', '\n'.join(errors), parent=win)
                return
            labels = tm.get_transition_labels()
            accept_states = set()
            if tm.accept_state:
                accept_states.add(tm.accept_state)
            self.canvas.reject_states = {tm.reject_state} if tm.reject_state else set()
            self.canvas.load_from_model(tm.states, tm.initial_state,
                                        accept_states, labels)
            self.tm = tm
            self._accept_var.set(tm.accept_state or '')
            self._reject_var.set(tm.reject_state or '')
            self.status_var.set(f'TM importada: {len(tm.states)} estados')
            self._clear_results()
            self._write_result('TM importada exitosamente.\n', 'info')
            win.destroy()

        ttk.Button(btn_frame, text='Importar', command=do_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cancelar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_export(self):
        if not self.canvas.states:
            messagebox.showinfo('Exportar', 'No hay automata para exportar.', parent=self)
            return

        tm = self._build_tm_from_canvas()
        lines = []
        lines.append(f'States: {", ".join(tm.states)}')
        lines.append(f'Input Alphabet: {", ".join(tm.input_alphabet)}')
        lines.append(f'Tape Alphabet: {", ".join(tm.tape_alphabet)}')
        lines.append(f'Initial: {tm.initial_state or ""}')
        lines.append(f'Accept: {tm.accept_state or ""}')
        lines.append(f'Reject: {tm.reject_state or ""}')
        lines.append('Transitions:')
        for (from_s, read_sym), (to_s, write_sym, direction) in sorted(tm.transitions.items()):
            lines.append(f'{from_s}, {read_sym} -> {to_s}, {write_sym}, {direction}')
        text = '\n'.join(lines)

        win = tk.Toplevel(self)
        win.title('Exportar TM como texto')
        win.geometry('650x450')
        win.minsize(550, 350)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Definicion de la Maquina de Turing:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))

        def copy_all():
            win.clipboard_clear()
            win.clipboard_append(text)
            self.status_var.set('Copiado al portapapeles')

        ttk.Button(btn_frame, text='Copiar', command=copy_all).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cerrar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        editor.insert('1.0', text)

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
