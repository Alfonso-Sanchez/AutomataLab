"""Base tab class for automaton/grammar editors."""

import tkinter as tk
from tkinter import ttk, scrolledtext


class BaseTab(ttk.Frame):
    """Base class for all automaton/grammar tabs."""

    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.title = title
        self._build_ui()

    def _build_ui(self):
        # Main horizontal paned window
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: definition editor
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)

        # Editor header with buttons
        header = ttk.Frame(left_frame)
        header.pack(fill=tk.X, pady=(0, 3))

        ttk.Label(header, text="Definicion:",
                   font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)

        self.example_var = tk.StringVar(value="Ejemplo 1")
        self.example_menu = ttk.Combobox(btn_frame, textvariable=self.example_var,
                                          values=["Ejemplo 1", "Ejemplo 2"],
                                          state='readonly', width=10)
        self.example_menu.pack(side=tk.LEFT, padx=2)
        self.example_menu.bind('<<ComboboxSelected>>', self._on_example_selected)

        self.btn_load = ttk.Button(btn_frame, text="Cargar",
                                    command=self._load_example)
        self.btn_load.pack(side=tk.LEFT, padx=2)

        self.btn_clear = ttk.Button(btn_frame, text="Limpiar",
                                     command=self._clear_editor)
        self.btn_clear.pack(side=tk.LEFT, padx=2)

        # Text editor
        self.editor = scrolledtext.ScrolledText(
            left_frame, wrap=tk.WORD, font=('Consolas', 11),
            bg='#1E1E1E', fg='#D4D4D4', insertbackground='white',
            selectbackground='#264F78', selectforeground='white',
            padx=8, pady=8
        )
        self.editor.pack(fill=tk.BOTH, expand=True)

        # Build button
        self.btn_build = ttk.Button(left_frame, text="Construir y Visualizar",
                                     command=self._on_build)
        self.btn_build.pack(fill=tk.X, pady=(5, 0))

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

        # Status / errors
        self.status_var = tk.StringVar(value="Listo. Escribe la definicion y presiona 'Construir'.")
        status_bar = ttk.Label(self, textvariable=self.status_var,
                                relief=tk.SUNKEN, anchor=tk.W,
                                font=('Segoe UI', 9))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_visualization(self, parent):
        """Override in subclasses to add visualization widget."""
        pass

    def _build_test_area(self, parent):
        """Build the string testing area."""
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="Cadena:").pack(side=tk.LEFT)
        self.test_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.test_entry.bind('<Return>', lambda e: self._on_test())

        self.btn_test = ttk.Button(input_frame, text="Probar",
                                    command=self._on_test)
        self.btn_test.pack(side=tk.LEFT, padx=2)

        self.btn_step = ttk.Button(input_frame, text="Paso a paso",
                                    command=self._on_step)
        self.btn_step.pack(side=tk.LEFT, padx=2)

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

    def _write_result(self, text, tag=None):
        """Append text to results area."""
        self.results.config(state='normal')
        if tag:
            self.results.insert(tk.END, text, tag)
        else:
            self.results.insert(tk.END, text)
        self.results.see(tk.END)
        self.results.config(state='disabled')

    def _clear_results(self):
        """Clear results area."""
        self.results.config(state='normal')
        self.results.delete('1.0', tk.END)
        self.results.config(state='disabled')

    def _on_build(self):
        """Override in subclasses."""
        pass

    def _on_test(self):
        """Override in subclasses."""
        pass

    def _on_step(self):
        """Override in subclasses - step-by-step simulation."""
        pass

    def _load_example(self):
        """Override in subclasses."""
        pass

    def _on_example_selected(self, event):
        """Handle example selection from combobox."""
        pass

    def _clear_editor(self):
        self.editor.delete('1.0', tk.END)

    def _get_editor_text(self):
        return self.editor.get('1.0', tk.END)

    def _set_editor_text(self, text):
        self.editor.delete('1.0', tk.END)
        self.editor.insert('1.0', text)
