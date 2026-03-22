"""CFG editor tab."""

import tkinter as tk
from tkinter import ttk, scrolledtext
from gui.base_tab import BaseTab
from core.cfg import CFG


class CFGTab(BaseTab):
    def __init__(self, parent):
        self.cfg = None
        self._tree_canvas = None
        self._last_parse_tree = None
        self._last_derivation = None
        super().__init__(parent, title="CFG")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_visualization(self, parent):
        """Build the right-side notebook with three tabs."""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # --- Tab 1: Parse Tree ---
        tree_frame = ttk.Frame(notebook)
        notebook.add(tree_frame, text="Arbol de Derivacion")

        self._tree_canvas = tk.Canvas(
            tree_frame, bg='#FAFAFA', highlightthickness=0
        )
        self._tree_canvas.pack(fill=tk.BOTH, expand=True)

        # Scrollbars for the tree canvas
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                       command=self._tree_canvas.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL,
                                       command=self._tree_canvas.xview)
        self._tree_canvas.configure(yscrollcommand=tree_scroll_y.set,
                                     xscrollcommand=tree_scroll_x.set)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y, before=self._tree_canvas)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X, before=self._tree_canvas)

        # --- Tab 2: Productions ---
        prod_frame = ttk.Frame(notebook)
        notebook.add(prod_frame, text="Producciones")

        self.prod_text = scrolledtext.ScrolledText(
            prod_frame, wrap=tk.WORD, font=('Consolas', 11),
            bg='#1E1E1E', fg='#D4D4D4', state='disabled',
            padx=8, pady=5
        )
        self.prod_text.pack(fill=tk.BOTH, expand=True)
        self.prod_text.tag_configure('variable', foreground='#64B5F6',
                                      font=('Consolas', 11, 'bold'))
        self.prod_text.tag_configure('arrow', foreground='#FF9800')
        self.prod_text.tag_configure('terminal', foreground='#81C784')
        self.prod_text.tag_configure('separator', foreground='#CE93D8')
        self.prod_text.tag_configure('title', foreground='#FFD54F',
                                      font=('Consolas', 11, 'bold'))
        self.prod_text.tag_configure('info', foreground='#90CAF9')

        # --- Tab 3: Generated strings ---
        gen_frame = ttk.Frame(notebook)
        notebook.add(gen_frame, text="Cadenas Generadas")

        gen_controls = ttk.Frame(gen_frame)
        gen_controls.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(gen_controls, text="Long. max:").pack(side=tk.LEFT)
        self.max_len_var = tk.IntVar(value=8)
        self.max_len_spin = ttk.Spinbox(gen_controls, from_=1, to=20,
                                         textvariable=self.max_len_var, width=5)
        self.max_len_spin.pack(side=tk.LEFT, padx=5)

        ttk.Label(gen_controls, text="Cantidad:").pack(side=tk.LEFT)
        self.max_count_var = tk.IntVar(value=20)
        self.max_count_spin = ttk.Spinbox(gen_controls, from_=1, to=100,
                                           textvariable=self.max_count_var, width=5)
        self.max_count_spin.pack(side=tk.LEFT, padx=5)

        self.btn_generate = ttk.Button(gen_controls, text="Generar",
                                        command=self._on_generate)
        self.btn_generate.pack(side=tk.LEFT, padx=5)

        self.gen_text = scrolledtext.ScrolledText(
            gen_frame, wrap=tk.WORD, font=('Consolas', 11),
            bg='#1A1A2E', fg='#E0E0E0', state='disabled',
            padx=8, pady=5
        )
        self.gen_text.pack(fill=tk.BOTH, expand=True)
        self.gen_text.tag_configure('string', foreground='#81C784')
        self.gen_text.tag_configure('info', foreground='#64B5F6')

        self._viz_notebook = notebook

    def _build_test_area(self, parent):
        """Build the string testing area with ambiguity button."""
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="Cadena:").pack(side=tk.LEFT)
        self.test_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.test_entry.bind('<Return>', lambda e: self._on_test())

        ttk.Button(
            input_frame, text="ε", width=2,
            command=lambda: self._insert_symbol_test("ε")
        ).pack(side=tk.LEFT, padx=1)

        self.btn_test = ttk.Button(input_frame, text="Probar",
                                    command=self._on_test)
        self.btn_test.pack(side=tk.LEFT, padx=2)

        self.btn_ambiguity = ttk.Button(input_frame, text="Verificar Ambiguedad",
                                         command=self._on_check_ambiguity)
        self.btn_ambiguity.pack(side=tk.LEFT, padx=2)

        # Results area
        self.results = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=('Consolas', 10),
            height=8, bg='#1A1A2E', fg='#E0E0E0',
            insertbackground='white', state='disabled',
            padx=8, pady=5
        )
        self.results.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Configure result tags
        self.results.tag_configure('accepted', foreground='#4CAF50',
                                    font=('Consolas', 10, 'bold'))
        self.results.tag_configure('rejected', foreground='#F44336',
                                    font=('Consolas', 10, 'bold'))
        self.results.tag_configure('error', foreground='#FF9800')
        self.results.tag_configure('info', foreground='#64B5F6')
        self.results.tag_configure('step', foreground='#CE93D8')
        self.results.tag_configure('ambiguous', foreground='#FF9800',
                                    font=('Consolas', 10, 'bold'))
        self.results.tag_configure('not_ambiguous', foreground='#4CAF50',
                                    font=('Consolas', 10, 'bold'))
        self.results.tag_configure('deriv_header', foreground='#FFD54F',
                                    font=('Consolas', 10, 'bold'))
        self.results.tag_configure('diff_highlight', foreground='#FF5252',
                                    font=('Consolas', 10, 'bold'))

    def _load_example(self):
        choice = self.example_var.get()
        if choice == "Ejemplo 2":
            self._set_editor_text(CFG.example2())
        elif choice == "Ejemplo 3":
            self._set_editor_text(CFG.example3())
        else:
            self._set_editor_text(CFG.example())

    def _on_example_selected(self, event):
        """Auto-load example on selection."""
        self._load_example()

    # ------------------------------------------------------------------
    # Symbol insertion helpers
    # ------------------------------------------------------------------

    def _insert_symbol_editor(self, sym):
        """Insert symbol at cursor position in the grammar editor."""
        self.editor.insert(tk.INSERT, sym)
        self.editor.focus_set()

    def _insert_symbol_test(self, sym):
        """Insert symbol at cursor position in the test entry."""
        self.test_entry.insert(tk.INSERT, sym)
        self.test_entry.focus_set()

    # ------------------------------------------------------------------
    # Test string
    # ------------------------------------------------------------------

    def _on_test(self):
        if self.cfg is None:
            self.status_var.set("Primero construye la CFG")
            return

        input_str = self.test_entry.get()
        self._clear_results()

        display_str = input_str if input_str else 'ε (cadena vacia)'
        self._write_result(f'Probando: "{display_str}"\n\n', 'info')

        # Use leftmost_derivation for richer info
        found, trail, msg = self.cfg.leftmost_derivation(input_str if input_str else '')

        if found and trail:
            self._last_derivation = trail
            self._write_result("Derivacion por la izquierda:\n", 'step')
            for i, (form, prod_info) in enumerate(trail):
                if i == 0:
                    self._write_result(f"  {form}\n")
                else:
                    var, prod = prod_info
                    self._write_result(f"  => {form}", 'step')
                    self._write_result(f"    [{var} -> {prod}]\n", 'info')
            self._write_result('\n')
            self._write_result("Resultado: ACEPTADA\n", 'accepted')

            # Build and draw parse tree
            tree = self.cfg.build_parse_tree(trail)
            if tree:
                self._last_parse_tree = tree
                self._draw_parse_tree(tree)
                self._viz_notebook.select(0)  # Switch to tree tab
        else:
            self._last_derivation = None
            self._last_parse_tree = None
            self._tree_canvas.delete('all')

            # Fall back to basic test
            accepted, derivation, basic_msg = self.cfg.test(input_str if input_str else '')
            if accepted and derivation:
                self._write_result("Derivacion:\n", 'step')
                for i, step in enumerate(derivation):
                    if i == 0:
                        self._write_result(f"  {step}\n")
                    else:
                        self._write_result(f"  => {step}\n")
                self._write_result('\n')
                self._write_result(f"Resultado: {basic_msg}\n", 'accepted')
            else:
                self._write_result(f"Resultado: {basic_msg}\n", 'rejected')

    def _on_step(self):
        self._on_test()

    # ------------------------------------------------------------------
    # Ambiguity check
    # ------------------------------------------------------------------

    def _on_check_ambiguity(self):
        if self.cfg is None:
            self.status_var.set("Primero construye la CFG")
            return

        input_str = self.test_entry.get()
        self._clear_results()

        display_str = input_str if input_str else 'ε (cadena vacia)'
        self._write_result(f'Verificando ambiguedad para: "{display_str}"\n\n', 'info')

        is_ambig, derivations, msg = self.cfg.is_ambiguous_for(
            input_str if input_str else ''
        )

        if is_ambig:
            self._write_result("AMBIGUA: ", 'ambiguous')
            self._write_result("Se encontraron multiples derivaciones por la izquierda.\n\n")

            for d_idx, deriv in enumerate(derivations[:2]):
                self._write_result(f"--- Derivacion {d_idx + 1} ---\n", 'deriv_header')
                for i, (form, prod_info) in enumerate(deriv):
                    if i == 0:
                        self._write_result(f"  {form}\n")
                    else:
                        var, prod = prod_info
                        # Check if this step differs between derivations
                        is_diff = False
                        if len(derivations) >= 2:
                            other = derivations[1 - d_idx] if d_idx < 2 else None
                            if other and i < len(other):
                                _, other_prod = other[i]
                                if other_prod != prod_info:
                                    is_diff = True

                        tag = 'diff_highlight' if is_diff else 'step'
                        self._write_result(f"  => {form}", tag)
                        prod_tag = 'diff_highlight' if is_diff else 'info'
                        self._write_result(f"    [{var} -> {prod}]\n", prod_tag)
                self._write_result('\n')

            self._write_result("Las lineas resaltadas en rojo indican donde difieren las derivaciones.\n", 'info')

            # Draw first parse tree
            if derivations:
                tree = self.cfg.build_parse_tree(derivations[0])
                if tree:
                    self._last_parse_tree = tree
                    self._draw_parse_tree(tree)
                    self._viz_notebook.select(0)

        elif derivations:
            self._write_result("NO AMBIGUA: ", 'not_ambiguous')
            self._write_result("La cadena tiene una unica derivacion por la izquierda.\n\n")

            deriv = derivations[0]
            self._write_result("Derivacion por la izquierda:\n", 'step')
            for i, (form, prod_info) in enumerate(deriv):
                if i == 0:
                    self._write_result(f"  {form}\n")
                else:
                    var, prod = prod_info
                    self._write_result(f"  => {form}", 'step')
                    self._write_result(f"    [{var} -> {prod}]\n", 'info')

            tree = self.cfg.build_parse_tree(deriv)
            if tree:
                self._last_parse_tree = tree
                self._draw_parse_tree(tree)
                self._viz_notebook.select(0)
        else:
            self._write_result(msg + '\n', 'rejected')

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def _on_import(self):
        win = tk.Toplevel(self)
        win.title('Importar CFG desde texto')
        win.geometry('500x400')
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Pega la definicion de la gramatica:',
                  font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))

        editor = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Consolas', 11),
                                           bg='#1E1E1E', fg='#D4D4D4',
                                           insertbackground='white', padx=8, pady=8)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def do_import():
            text = editor.get('1.0', tk.END)
            cfg, errors = CFG.parse(text)
            if errors:
                from tkinter import messagebox
                messagebox.showerror('Errores de parseo', '\n'.join(errors), parent=win)
                return
            self._set_editor_text(text.strip())
            self.cfg = cfg
            self._on_build()
            self.status_var.set(f'CFG importada: {len(cfg.variables)} variables')
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text='Importar', command=do_import).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text='Cancelar', command=win.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_export(self):
        text = self._get_editor_text().strip()
        if not text:
            from tkinter import messagebox
            messagebox.showinfo('Exportar', 'No hay gramatica definida.', parent=self)
            return

        win = tk.Toplevel(self)
        win.title('Exportar CFG como texto')
        win.geometry('500x350')
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text='Definicion de la CFG:',
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

    # ------------------------------------------------------------------
    # Generate strings
    # ------------------------------------------------------------------

    def _on_generate(self):
        if self.cfg is None:
            self.status_var.set("Primero construye la CFG")
            return

        max_len = self.max_len_var.get()
        max_count = self.max_count_var.get()

        strings = self.cfg.generate_strings(max_length=max_len, max_count=max_count)

        self.gen_text.config(state='normal')
        self.gen_text.delete('1.0', tk.END)
        self.gen_text.insert(tk.END,
                             f"Cadenas generadas (max longitud={max_len}):\n\n", 'info')

        if strings:
            for i, s in enumerate(strings, 1):
                display = s if s != 'ε' else 'ε (cadena vacia)'
                self.gen_text.insert(tk.END, f"  {i:3d}. ", 'info')
                self.gen_text.insert(tk.END, f"{display}\n", 'string')
            self.gen_text.insert(tk.END, f"\nTotal: {len(strings)} cadenas\n", 'info')
        else:
            self.gen_text.insert(tk.END, "No se pudieron generar cadenas.\n", 'info')

        self.gen_text.config(state='disabled')

    # ------------------------------------------------------------------
    # Parse tree drawing on Canvas
    # ------------------------------------------------------------------

    def _draw_parse_tree(self, tree):
        """Draw the parse tree on the canvas."""
        canvas = self._tree_canvas
        canvas.delete('all')

        if tree is None:
            return

        # Layout parameters
        node_radius = 18
        h_spacing = 40
        v_spacing = 65
        top_margin = 40
        left_margin = 30
        font = ('Consolas', 10)

        # First pass: count leaves to determine widths
        self._count_leaves(tree)

        # Second pass: assign positions
        total_leaves = tree.get('_leaves', 1)
        total_width = total_leaves * h_spacing + left_margin * 2
        canvas_width = max(total_width, 400)

        self._assign_positions(tree, left_margin, top_margin,
                               canvas_width - left_margin, v_spacing)

        # Calculate canvas bounds
        max_x, max_y = self._get_tree_bounds(tree)
        canvas.configure(scrollregion=(0, 0, max_x + 60, max_y + 60))

        # Draw edges first (so nodes appear on top)
        self._draw_edges(canvas, tree)

        # Draw nodes
        self._draw_nodes(canvas, tree, node_radius, font)

    def _count_leaves(self, node):
        """Count the number of leaves under each node."""
        if not node['children']:
            node['_leaves'] = 1
            return 1
        total = 0
        for child in node['children']:
            total += self._count_leaves(child)
        node['_leaves'] = total
        return total

    def _assign_positions(self, node, left, top, right, v_spacing):
        """Assign (x, y) positions to each node in the tree."""
        node['_y'] = top

        if not node['children']:
            node['_x'] = (left + right) / 2
            return

        # Distribute horizontal space among children proportional to leaf count
        total_leaves = sum(c.get('_leaves', 1) for c in node['children'])
        available_width = right - left

        current_left = left
        for child in node['children']:
            child_leaves = child.get('_leaves', 1)
            child_width = (child_leaves / total_leaves) * available_width
            child_right = current_left + child_width
            self._assign_positions(child, current_left, top + v_spacing,
                                   child_right, v_spacing)
            current_left = child_right

        # Parent x is average of children x
        child_xs = [c['_x'] for c in node['children']]
        node['_x'] = (min(child_xs) + max(child_xs)) / 2

    def _get_tree_bounds(self, node):
        """Get the maximum x and y coordinates in the tree."""
        max_x = node.get('_x', 0)
        max_y = node.get('_y', 0)
        for child in node['children']:
            cx, cy = self._get_tree_bounds(child)
            max_x = max(max_x, cx)
            max_y = max(max_y, cy)
        return max_x, max_y

    def _draw_edges(self, canvas, node):
        """Draw lines from parent to children."""
        px, py = node['_x'], node['_y']
        for child in node['children']:
            cx, cy = child['_x'], child['_y']
            canvas.create_line(px, py + 18, cx, cy - 18,
                               fill='#616161', width=1.5)
            self._draw_edges(canvas, child)

    def _draw_nodes(self, canvas, node, radius, font):
        """Draw node symbols on the canvas."""
        x, y = node['_x'], node['_y']
        symbol = node['symbol']
        is_var = self.cfg and self.cfg._is_variable(symbol)
        is_epsilon = symbol in ('ε', 'eps')

        if is_var and node['children']:
            # Variable (expanded): blue circle
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                               fill='#E3F2FD', outline='#1565C0', width=2)
            canvas.create_text(x, y, text=symbol, font=font,
                               fill='#1565C0')
        elif is_var and not node['children']:
            # Variable (unexpanded leaf): dashed blue circle
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                               fill='#E3F2FD', outline='#1565C0', width=2,
                               dash=(4, 2))
            canvas.create_text(x, y, text=symbol, font=font,
                               fill='#1565C0')
        elif is_epsilon:
            # Epsilon terminal: italic grey
            canvas.create_rectangle(x - radius, y - radius,
                                    x + radius, y + radius,
                                    fill='#F5F5F5', outline='#9E9E9E', width=1.5)
            canvas.create_text(x, y, text='ε', font=('Consolas', 10, 'italic'),
                               fill='#9E9E9E')
        else:
            # Terminal: green rectangle
            text_width = max(radius, len(symbol) * 6 + 8)
            canvas.create_rectangle(x - text_width // 2, y - radius,
                                    x + text_width // 2, y + radius,
                                    fill='#E8F5E9', outline='#1B5E20', width=2)
            canvas.create_text(x, y, text=symbol, font=font,
                               fill='#1B5E20')

        # Recurse into children
        for child in node['children']:
            self._draw_nodes(canvas, child, radius, font)

    # ------------------------------------------------------------------
    # Override base_tab setup to add example 3
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Override to customize the example combobox with 3 examples."""
        # Main horizontal paned window
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: definition editor
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)

        # Editor header
        header = ttk.Frame(left_frame)
        header.pack(fill=tk.X, pady=(0, 3))

        ttk.Label(header, text="Definicion de la gramatica:",
                   font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)

        self.example_var = tk.StringVar(value="Ejemplo 1")
        self.example_menu = ttk.Combobox(
            btn_frame, textvariable=self.example_var,
            values=["Ejemplo 1", "Ejemplo 2", "Ejemplo 3"],
            state='readonly', width=10
        )
        self.example_menu.pack(side=tk.LEFT, padx=2)
        self.example_menu.bind('<<ComboboxSelected>>', self._on_example_selected)

        self.btn_load = ttk.Button(btn_frame, text="Cargar",
                                    command=self._load_example)
        self.btn_load.pack(side=tk.LEFT, padx=2)

        self.btn_clear = ttk.Button(btn_frame, text="Limpiar",
                                     command=self._clear_editor)
        self.btn_clear.pack(side=tk.LEFT, padx=2)

        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        ttk.Button(btn_frame, text="Importar",
                   command=self._on_import).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Exportar",
                   command=self._on_export).pack(side=tk.LEFT, padx=2)

        # Symbol insertion buttons
        sym_frame = ttk.Frame(left_frame)
        sym_frame.pack(fill=tk.X, pady=(3, 3))
        ttk.Label(sym_frame, text="Insertar:").pack(side=tk.LEFT)
        for sym, tip in [("ε", "epsilon"), ("→", "flecha"),
                         ("|", "alternativa"), ("λ", "lambda")]:
            btn = ttk.Button(
                sym_frame, text=sym, width=3,
                command=lambda s=sym: self._insert_symbol_editor(s)
            )
            btn.pack(side=tk.LEFT, padx=1)

        # Text editor
        self.editor = scrolledtext.ScrolledText(
            left_frame, wrap=tk.WORD, font=('Consolas', 11),
            bg='#1E1E1E', fg='#D4D4D4', insertbackground='white',
            selectbackground='#264F78', selectforeground='white',
            padx=8, pady=8
        )
        self.editor.pack(fill=tk.BOTH, expand=True)

        # Build button
        self.btn_build = ttk.Button(left_frame, text="Construir",
                                     command=self._on_build)
        self.btn_build.pack(fill=tk.X, pady=(5, 0))

        # Formal definition display
        self.formal_frame = ttk.LabelFrame(left_frame, text="Definicion formal")
        self.formal_frame.pack(fill=tk.X, pady=(5, 0))

        self.formal_text = tk.Text(
            self.formal_frame, wrap=tk.WORD, font=('Consolas', 10),
            bg='#263238', fg='#B0BEC5', height=5, state='disabled',
            padx=6, pady=4, relief=tk.FLAT
        )
        self.formal_text.pack(fill=tk.X, padx=3, pady=3)
        self.formal_text.tag_configure('var', foreground='#64B5F6')
        self.formal_text.tag_configure('term', foreground='#81C784')
        self.formal_text.tag_configure('label', foreground='#FFD54F',
                                        font=('Consolas', 10, 'bold'))

        # Right panel: visualization + testing
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=1)

        right_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        right_paned.pack(fill=tk.BOTH, expand=True)

        # Visualization area
        viz_frame = ttk.LabelFrame(right_frame, text="Visualizacion")
        right_paned.add(viz_frame, weight=2)
        self._build_visualization(viz_frame)

        # Testing area
        test_frame = ttk.LabelFrame(right_frame, text="Probar Cadenas")
        right_paned.add(test_frame, weight=1)
        self._build_test_area(test_frame)

        # Status bar
        self.status_var = tk.StringVar(
            value="Listo. Escribe la definicion y presiona 'Construir'."
        )
        status_bar = ttk.Label(self, textvariable=self.status_var,
                                relief=tk.SUNKEN, anchor=tk.W,
                                font=('Segoe UI', 9))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _update_formal_definition(self, cfg):
        """Update the formal definition display below the editor."""
        self.formal_text.config(state='normal')
        self.formal_text.delete('1.0', tk.END)

        vars_str = ', '.join(sorted(cfg.variables))
        terms_str = ', '.join(sorted(cfg.terminals))

        self.formal_text.insert(tk.END, "G = (V, Sigma, R, S)\n", 'label')
        self.formal_text.insert(tk.END, "V = ", 'label')
        self.formal_text.insert(tk.END, f"{{{vars_str}}}\n", 'var')
        self.formal_text.insert(tk.END, "Sigma = ", 'label')
        self.formal_text.insert(tk.END, f"{{{terms_str}}}\n", 'term')
        self.formal_text.insert(tk.END, "S = ", 'label')
        self.formal_text.insert(tk.END, f"{cfg.start_symbol}\n", 'var')

        total_prods = sum(len(v) for v in cfg.productions.values())
        self.formal_text.insert(tk.END, f"|R| = {total_prods} producciones\n", 'label')

        self.formal_text.config(state='disabled')

    def _on_build(self):
        text = self._get_editor_text()
        cfg, errors = CFG.parse(text)
        if errors:
            self.status_var.set(f"Errores: {'; '.join(errors)}")
            self._clear_results()
            self._write_result("ERRORES DE CONSTRUCCION:\n", 'error')
            for e in errors:
                self._write_result(f"  - {e}\n", 'error')
            # Clear formal definition on error
            self.formal_text.config(state='normal')
            self.formal_text.delete('1.0', tk.END)
            self.formal_text.config(state='disabled')
            return

        self.cfg = cfg
        self._last_parse_tree = None
        self._last_derivation = None
        self._tree_canvas.delete('all')

        # Update formal definition
        self._update_formal_definition(cfg)

        # --- Productions tab ---
        self.prod_text.config(state='normal')
        self.prod_text.delete('1.0', tk.END)

        vars_str = ', '.join(sorted(cfg.variables))
        terms_str = ', '.join(sorted(cfg.terminals))

        self.prod_text.insert(tk.END, "Definicion formal:\n", 'title')
        self.prod_text.insert(tk.END, f"  G = (V, Sigma, R, {cfg.start_symbol})\n", 'info')
        self.prod_text.insert(tk.END, f"  V = {{{vars_str}}}\n", 'variable')
        self.prod_text.insert(tk.END, f"  Sigma = {{{terms_str}}}\n", 'terminal')
        self.prod_text.insert(tk.END, f"  S = {cfg.start_symbol}\n\n", 'info')

        self.prod_text.insert(tk.END, "Producciones (R):\n", 'title')

        for var in sorted(cfg.productions.keys(),
                          key=lambda v: (v != cfg.start_symbol, v)):
            self.prod_text.insert(tk.END, f"  {var}", 'variable')
            self.prod_text.insert(tk.END, " -> ", 'arrow')
            prods = cfg.productions[var]
            for i, prod in enumerate(prods):
                if i > 0:
                    self.prod_text.insert(tk.END, " | ", 'separator')
                for ch in prod:
                    if ch.isupper() and ch in cfg.variables:
                        self.prod_text.insert(tk.END, ch, 'variable')
                    else:
                        self.prod_text.insert(tk.END, ch, 'terminal')
            self.prod_text.insert(tk.END, "\n")

        self.prod_text.config(state='disabled')

        total_prods = sum(len(v) for v in cfg.productions.values())
        self.status_var.set(
            f"CFG construida: {len(cfg.variables)} variables, "
            f"{len(cfg.terminals)} terminales, "
            f"{total_prods} producciones"
        )
        self._clear_results()
        self._write_result("CFG construida exitosamente.\n", 'info')
        self._write_result(f"  G = ({{{vars_str}}}, {{{terms_str}}}, R, {cfg.start_symbol})\n\n", 'info')
        self._write_result("Puedes probar cadenas o generar cadenas del lenguaje.\n")
        self._write_result("Usa 'Verificar Ambiguedad' para comprobar si una cadena es ambigua.\n")
