"""Interactive canvas-based automata builder using tkinter Canvas."""

import math
import tkinter as tk
from tkinter import ttk, filedialog


class AutomataCanvas(ttk.Frame):
    """Composite widget: toolbar + interactive canvas for building automata visually."""

    BASE_STATE_RADIUS = 28
    COLORS = {
        'bg': '#FAFAFA',
        'state_fill': '#E3F2FD',
        'state_border': '#1565C0',
        'accept_border': '#1B5E20',
        'accept_fill': '#E8F5E9',
        'initial_arrow': '#333333',
        'transition': '#555555',
        'transition_text': '#222222',
        'highlight_fill': '#FFF9C4',
        'highlight_border': '#F57F17',
        'reject_fill': '#FFCDD2',
        'reject_border': '#C62828',
        'accept_highlight_fill': '#C8E6C9',
        'accept_highlight_border': '#2E7D32',
        'hover_fill': '#BBDEFB',
        'selected_border': '#FF6F00',
        'delete_fill': '#FFCDD2',
    }

    MODES = {
        'select': 'Seleccionar',
        'add_state': 'Estado',
        'add_transition': 'Transicion',
        'set_initial': 'Inicial',
        'set_accept': 'Aceptacion',
        'set_reject': 'Rechazo',
        'delete': 'Eliminar',
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self._on_change_callback = None
        self._transition_dialog_callback = None
        self.automaton_type = 'Automata'  # DFA, NFA, PDA - set by parent tab

        # --- Data model ---
        self.states = {}       # name -> {'x': float, 'y': float, 'is_initial': bool, 'is_accept': bool}
        self.transitions = []  # [{'from': str, 'to': str, 'label': str}]
        self.reject_states = set()  # For TM: states that are reject states

        # --- Interaction state ---
        self._mode = 'select'
        self._drag_state = None
        self._drag_offset = (0, 0)
        self._transition_source = None
        self._hover_state = None
        self._selected_state = None
        self._highlighted_states = {}

        # --- Zoom / Pan state ---
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._pan_dragging = False
        self._pan_start = (0, 0)

        # --- Build UI ---
        self._build_toolbar()
        self.canvas = tk.Canvas(self, bg=self.COLORS['bg'], highlightthickness=0,
                                **kwargs)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- Bindings ---
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<Motion>', self._on_motion)
        self.canvas.bind('<Configure>', lambda e: self._redraw())

        # Zoom with mousewheel
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        # Pan with middle mouse button
        self.canvas.bind('<Button-2>', self._on_pan_start)
        self.canvas.bind('<B2-Motion>', self._on_pan_drag)
        self.canvas.bind('<ButtonRelease-2>', self._on_pan_end)
        # Also support Shift+drag for pan (more common on laptops)
        self.canvas.bind('<Shift-Button-1>', self._on_pan_start)
        self.canvas.bind('<Shift-B1-Motion>', self._on_pan_drag)
        self.canvas.bind('<Shift-ButtonRelease-1>', self._on_pan_end)

    # ──────────────────────────────────────────────
    # Toolbar
    # ──────────────────────────────────────────────

    def _build_toolbar(self):
        toolbar_container = ttk.Frame(self)
        toolbar_container.pack(fill=tk.X, padx=2, pady=(2, 0))

        # Row 1: Mode buttons
        row1 = ttk.Frame(toolbar_container)
        row1.pack(fill=tk.X)
        row1.columnconfigure(100, weight=1)  # spacer column

        self._mode_buttons = {}
        modes_config = [
            ('select', '\u270b Mover'),
            ('add_state', '\u2795 Estado'),
            ('add_transition', '\u27a1 Trans.'),
            ('set_initial', '\U0001f3c1 Inicial'),
            ('set_accept', '\u2713 Acept.'),
            ('delete', '\U0001f5d1 Eliminar'),
        ]
        for col, (mode_key, label) in enumerate(modes_config):
            btn = ttk.Button(row1, text=label,
                             command=lambda m=mode_key: self.set_mode(m))
            btn.grid(row=0, column=col, padx=1, pady=1, sticky=tk.W)
            self._mode_buttons[mode_key] = btn

        self._mode_label = ttk.Label(row1, text='Modo: Seleccionar',
                                     font=('Segoe UI', 8, 'italic'))
        self._mode_label.grid(row=0, column=100, padx=4, sticky=tk.E)

        # Row 2: Clear + Zoom + Export
        row2 = ttk.Frame(toolbar_container)
        row2.pack(fill=tk.X)
        row2.columnconfigure(10, weight=1)  # spacer column

        self._btn_clear = ttk.Button(row2, text='\U0001f9f9 Limpiar',
                                     command=self.clear_all)
        self._btn_clear.grid(row=0, column=0, padx=1, pady=1, sticky=tk.W)

        # Zoom controls on the right
        self._zoom_label = ttk.Label(row2, text='100%',
                                     font=('Segoe UI', 8), width=5, anchor=tk.CENTER)
        self._zoom_label.grid(row=0, column=11, padx=2)
        ttk.Button(row2, text='+', width=2,
                   command=lambda: self._zoom_by(1.25)).grid(row=0, column=12, padx=0, pady=1)
        ttk.Button(row2, text='\u2212', width=2,
                   command=lambda: self._zoom_by(0.8)).grid(row=0, column=13, padx=0, pady=1)
        ttk.Button(row2, text='Reset', width=5,
                   command=self._reset_view).grid(row=0, column=14, padx=1, pady=1)
        ttk.Button(row2, text='\U0001f4f7 Foto', width=6,
                   command=self._export_image).grid(row=0, column=15, padx=1, pady=1)

        self.toolbar = toolbar_container

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def set_mode(self, mode):
        """Change the current interaction mode."""
        self._mode = mode
        self._transition_source = None
        label = self.MODES.get(mode, mode)
        self._mode_label.config(text=f'Modo: {label}')
        # Update button relief to show active mode
        for key, btn in self._mode_buttons.items():
            if key == mode:
                btn.state(['pressed'])
            else:
                btn.state(['!pressed'])
        self._redraw()

    def get_states(self):
        """Return copy of states dict."""
        return dict(self.states)

    def get_transitions(self):
        """Return copy of transitions list."""
        return list(self.transitions)

    def load_from_model(self, states, initial, accept, transition_labels):
        """Load automaton from core model data.

        Args:
            states: list of state names
            initial: initial state name
            accept: set of accept state names
            transition_labels: dict of (from, to) -> label_string
        """
        self.states = {}
        self.transitions = []
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0

        if not states:
            self._redraw()
            return

        # Layout in circle (world coordinates)
        self.canvas.update_idletasks()
        w = max(self.canvas.winfo_width(), 450)
        h = max(self.canvas.winfo_height(), 350)
        cx, cy = w / 2, h / 2
        n = len(states)

        for i, name in enumerate(states):
            if n == 1:
                x, y = cx, cy
            else:
                radius = min(w, h) * 0.35
                angle = -math.pi / 2 + 2 * math.pi * i / n
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
            self.states[name] = {
                'x': x, 'y': y,
                'is_initial': (name == initial),
                'is_accept': (name in accept),
            }

        # Parse transition labels
        for (from_s, to_s), label_str in transition_labels.items():
            for lbl in label_str.split('\n'):
                lbl = lbl.strip()
                if lbl:
                    self.transitions.append({'from': from_s, 'to': to_s, 'label': lbl})

        self._redraw()

    def clear_all(self):
        """Reset canvas to empty."""
        self.states = {}
        self.transitions = []
        self._drag_state = None
        self._transition_source = None
        self._hover_state = None
        self._selected_state = None
        self._highlighted_states = {}
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._zoom_label.config(text='100%')
        self._redraw()
        self._fire_change()

    def set_transition_dialog(self, callback):
        """Set callback for transition input dialog.
        Signature: callback(from_state, to_state) -> label_str or None
        """
        self._transition_dialog_callback = callback

    def highlight_states(self, state_names, highlight_type='normal'):
        """Highlight specific states for test visualization.

        Args:
            state_names: iterable of state names, or None to clear highlights.
            highlight_type: 'normal' (yellow), 'accept' (green), 'reject' (red)
        """
        self._highlighted_states = {}
        if state_names:
            for name in state_names:
                if name in self.states:
                    self._highlighted_states[name] = highlight_type
        self._redraw()

    def clear_highlights(self):
        """Clear all state highlights."""
        self._highlighted_states = {}
        self._redraw()

    def set_on_change(self, callback):
        """Set callback invoked when automaton model changes (states/transitions modified)."""
        self._on_change_callback = callback

    def register_mode_button(self, mode_key, btn):
        """Register an external button as a mode toggle (so it highlights with the active mode)."""
        self._mode_buttons[mode_key] = btn

    @property
    def STATE_RADIUS(self):
        return self.BASE_STATE_RADIUS * self._zoom

    # ──────────────────────────────────────────────
    # State rename helper
    # ──────────────────────────────────────────────

    def _rename_state(self, old_name, new_name):
        """Rename a state in-place, updating all transitions and sets."""
        if old_name == new_name or old_name not in self.states:
            return
        self.states[new_name] = self.states.pop(old_name)
        for t in self.transitions:
            if t['from'] == old_name:
                t['from'] = new_name
            if t['to'] == old_name:
                t['to'] = new_name
        if old_name in self.reject_states:
            self.reject_states.discard(old_name)
            self.reject_states.add(new_name)
        if self._selected_state == old_name:
            self._selected_state = new_name
        if self._hover_state == old_name:
            self._hover_state = new_name

    # ──────────────────────────────────────────────
    # Smart state ID: reuse lowest available qN
    # ──────────────────────────────────────────────

    def _next_available_state_name(self):
        """Find the lowest qN name not currently in use."""
        used = set()
        for name in self.states:
            if name.startswith('q'):
                try:
                    used.add(int(name[1:]))
                except ValueError:
                    pass
        n = 0
        while n in used:
            n += 1
        return f'q{n}'

    # ──────────────────────────────────────────────
    # Coordinate transforms (world <-> screen)
    # ──────────────────────────────────────────────

    def _world_to_screen(self, wx, wy):
        """Convert world (model) coordinates to screen (canvas) coordinates."""
        sx = wx * self._zoom + self._pan_x
        sy = wy * self._zoom + self._pan_y
        return sx, sy

    def _screen_to_world(self, sx, sy):
        """Convert screen (canvas) coordinates to world (model) coordinates."""
        wx = (sx - self._pan_x) / self._zoom
        wy = (sy - self._pan_y) / self._zoom
        return wx, wy

    # ──────────────────────────────────────────────
    # Zoom / Pan
    # ──────────────────────────────────────────────

    def _zoom_by(self, factor):
        """Zoom centered on canvas middle."""
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        # Adjust pan so center stays fixed
        self._pan_x = cx - (cx - self._pan_x) * factor
        self._pan_y = cy - (cy - self._pan_y) * factor
        self._zoom *= factor
        self._zoom = max(0.2, min(5.0, self._zoom))
        self._zoom_label.config(text=f'{int(self._zoom * 100)}%')
        self._redraw()

    def _reset_view(self):
        """Reset zoom and pan to defaults."""
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._zoom_label.config(text='100%')
        self._redraw()

    def _on_mousewheel(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        # Zoom centered on mouse position
        mx, my = event.x, event.y
        self._pan_x = mx - (mx - self._pan_x) * factor
        self._pan_y = my - (my - self._pan_y) * factor
        self._zoom *= factor
        self._zoom = max(0.2, min(5.0, self._zoom))
        self._zoom_label.config(text=f'{int(self._zoom * 100)}%')
        self._redraw()

    def _on_pan_start(self, event):
        self._pan_dragging = True
        self._pan_start = (event.x, event.y)

    def _on_pan_drag(self, event):
        if self._pan_dragging:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self._pan_x += dx
            self._pan_y += dy
            self._pan_start = (event.x, event.y)
            self._redraw()

    def _on_pan_end(self, event):
        self._pan_dragging = False

    # ──────────────────────────────────────────────
    # Export to image
    # ──────────────────────────────────────────────

    def _export_image(self):
        """Export the canvas as a PNG image using Pillow (no Ghostscript needed)."""
        if not self.states:
            return

        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f'{self.automaton_type}_{timestamp}.png'

        filepath = filedialog.asksaveasfilename(
            defaultextension='.png',
            initialfile=default_name,
            filetypes=[('PNG', '*.png'), ('All files', '*.*')],
            title='Exportar diagrama como imagen'
        )
        if not filepath:
            return
        try:
            from PIL import Image, ImageDraw, ImageFont

            margin = 100
            xs = [d['x'] for d in self.states.values()]
            ys = [d['y'] for d in self.states.values()]
            min_x = min(xs) - margin
            min_y = min(ys) - margin
            max_x = max(xs) + margin
            max_y = max(ys) + margin

            scale = 2
            w = int((max_x - min_x) * scale)
            h = int((max_y - min_y) * scale)
            img = Image.new('RGB', (w, h), 'white')
            draw = ImageDraw.Draw(img)

            r = self.BASE_STATE_RADIUS * scale
            arrow_size = 10 * scale

            try:
                font = ImageFont.truetype("consola.ttf", 13 * scale)
                font_sm = ImageFont.truetype("consola.ttf", 10 * scale)
            except (OSError, IOError):
                font = ImageFont.load_default()
                font_sm = font

            def to_img(wx, wy):
                return int((wx - min_x) * scale), int((wy - min_y) * scale)

            def draw_centered(x, y, text, fnt, fill='#222222'):
                """Draw text centered at (x, y), handling single and multiline."""
                if '\n' in text:
                    try:
                        bbox = draw.multiline_textbbox((0, 0), text, font=fnt)
                    except AttributeError:
                        bbox = (0, 0, 60, 30)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    draw.multiline_text((x - tw // 2, y - th // 2), text,
                                       fill=fill, font=fnt, align='center')
                else:
                    try:
                        draw.text((x, y), text, fill=fill, font=fnt, anchor='mm')
                    except TypeError:
                        try:
                            bbox = draw.textbbox((0, 0), text, font=fnt)
                        except AttributeError:
                            bbox = (0, 0, len(text) * 8, 16)
                        tw = bbox[2] - bbox[0]
                        th = bbox[3] - bbox[1]
                        draw.text((x - tw // 2, y - th // 2), text, fill=fill, font=fnt)

            def draw_arrowhead(x1, y1, x2, y2, color='#555555', size=None):
                """Draw a filled arrowhead at (x2, y2) pointing from (x1,y1)."""
                sz = size or arrow_size
                dx = x2 - x1
                dy = y2 - y1
                dist = math.sqrt(dx * dx + dy * dy)
                if dist == 0:
                    return
                ndx, ndy = dx / dist, dy / dist
                # Base of arrowhead
                bx = x2 - ndx * sz
                by = y2 - ndy * sz
                # Perpendicular
                px, py = -ndy * sz * 0.4, ndx * sz * 0.4
                points = [(x2, y2), (bx + px, by + py), (bx - px, by - py)]
                draw.polygon(points, fill=color)

            # Group transitions
            grouped = {}
            pair_set = set()
            for t in self.transitions:
                pair_set.add((t['from'], t['to']))
                key = (t['from'], t['to'])
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(t['label'])

            # Draw transitions
            for (from_s, to_s), labels in grouped.items():
                if from_s not in self.states or to_s not in self.states:
                    continue
                sf = self.states[from_s]
                st = self.states[to_s]
                x1, y1 = to_img(sf['x'], sf['y'])
                x2, y2 = to_img(st['x'], st['y'])
                label = ', '.join(labels) if all(len(l) <= 3 for l in labels) else '\n'.join(labels)

                if from_s == to_s:
                    loop_r = int(20 * scale)
                    cx, cy = x1, y1 - int(r) - loop_r
                    draw.ellipse([cx - loop_r, cy - loop_r, cx + loop_r, cy + loop_r],
                                 outline='#555555', width=max(2, scale))
                    draw_centered(cx, cy - loop_r - 12 * scale, label, font_sm)
                else:
                    # Line from edge of source to edge of target
                    dx = x2 - x1
                    dy = y2 - y1
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist == 0:
                        continue
                    ndx, ndy = dx / dist, dy / dist

                    has_reverse = (to_s, from_s) in pair_set
                    if has_reverse:
                        offset = 8 * scale
                        px, py = -ndy * offset, ndx * offset
                    else:
                        px, py = 0, 0

                    sx = x1 + ndx * r + px
                    sy = y1 + ndy * r + py
                    ex = x2 - ndx * r + px
                    ey = y2 - ndy * r + py

                    draw.line([(int(sx), int(sy)), (int(ex), int(ey))],
                              fill='#555555', width=max(2, scale))
                    draw_arrowhead(sx, sy, ex, ey)

                    # Label at midpoint
                    mx = (sx + ex) / 2 - ndy * 14 * scale
                    my = (sy + ey) / 2 + ndx * 14 * scale
                    draw_centered(int(mx), int(my), label, font_sm)

            # Draw initial arrows
            for name, data in self.states.items():
                if data['is_initial']:
                    ix, iy = to_img(data['x'], data['y'])
                    arrow_len = 35 * scale
                    start_x = ix - int(r) - int(arrow_len)
                    end_x = ix - int(r)
                    draw.line([(start_x, iy), (end_x, iy)],
                              fill='#333333', width=max(2, scale))
                    draw_arrowhead(start_x, iy, end_x, iy, color='#333333')

            # Draw states
            for name, data in self.states.items():
                cx, cy = to_img(data['x'], data['y'])
                is_accept = data['is_accept']
                is_reject = name in self.reject_states

                if is_reject:
                    fill_c = '#FFCDD2'
                    outline_c = '#C62828'
                elif is_accept:
                    fill_c = '#E8F5E9'
                    outline_c = '#1B5E20'
                else:
                    fill_c = '#E3F2FD'
                    outline_c = '#1565C0'

                draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                             fill=fill_c, outline=outline_c, width=3)
                if is_accept:
                    ir = r - 5 * scale
                    draw.ellipse([cx - ir, cy - ir, cx + ir, cy + ir],
                                 fill=fill_c, outline=outline_c, width=3)
                draw_centered(cx, cy, name, font, fill=outline_c)
                if is_reject:
                    off = int(r * 0.55)
                    draw.line([(cx - off, cy - off), (cx + off, cy + off)],
                              fill=outline_c, width=max(2, scale))
                    draw.line([(cx - off, cy + off), (cx + off, cy - off)],
                              fill=outline_c, width=max(2, scale))

            img.save(filepath)
            from tkinter import messagebox
            messagebox.showinfo('Exportar', f'Imagen guardada:\n{filepath}', parent=self)
        except ImportError:
            from tkinter import messagebox
            messagebox.showerror(
                'Error al exportar',
                'Pillow no esta instalado.\nEjecuta: pip install Pillow',
                parent=self
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror('Error al exportar', str(e), parent=self)

    # ──────────────────────────────────────────────
    # Event handlers
    # ──────────────────────────────────────────────

    def _fire_change(self):
        if self._on_change_callback:
            self._on_change_callback()

    def _state_at(self, sx, sy):
        """Return state name at screen position, or None."""
        wx, wy = self._screen_to_world(sx, sy)
        r = self.BASE_STATE_RADIUS + 4
        for name, data in self.states.items():
            dx = wx - data['x']
            dy = wy - data['y']
            if dx * dx + dy * dy <= r * r:
                return name
        return None

    def _transition_at(self, sx, sy):
        """Return index of transition near screen position, or None."""
        wx, wy = self._screen_to_world(sx, sy)
        threshold = 12
        for i, t in enumerate(self.transitions):
            if t['from'] not in self.states or t['to'] not in self.states:
                continue
            s = self.states[t['from']]
            e = self.states[t['to']]

            if t['from'] == t['to']:
                loop_cx = s['x']
                loop_cy = s['y'] - self.BASE_STATE_RADIUS - 20
                dist = math.sqrt((wx - loop_cx) ** 2 + (wy - loop_cy) ** 2)
                if abs(dist - 20) < threshold:
                    return i
            else:
                dist = self._point_to_segment_dist(wx, wy, s['x'], s['y'], e['x'], e['y'])
                if dist < threshold:
                    return i
        return None

    @staticmethod
    def _point_to_segment_dist(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

    def _on_click(self, event):
        x, y = event.x, event.y
        clicked_state = self._state_at(x, y)

        if self._mode == 'select':
            if clicked_state:
                self._drag_state = clicked_state
                data = self.states[clicked_state]
                wx, wy = self._screen_to_world(x, y)
                self._drag_offset = (wx - data['x'], wy - data['y'])
                self._selected_state = clicked_state
            else:
                self._selected_state = None
            self._redraw()

        elif self._mode == 'add_state':
            if not clicked_state:
                name = self._next_available_state_name()
                wx, wy = self._screen_to_world(x, y)
                is_initial = len(self.states) == 0
                self.states[name] = {
                    'x': wx, 'y': wy,
                    'is_initial': is_initial,
                    'is_accept': False,
                }
                if is_initial:
                    for other_name, other_data in self.states.items():
                        if other_name != name:
                            other_data['is_initial'] = False
                self._redraw()
                self._fire_change()

        elif self._mode == 'add_transition':
            if clicked_state:
                if self._transition_source is None:
                    self._transition_source = clicked_state
                    self._selected_state = clicked_state
                    self._redraw()
                else:
                    source = self._transition_source
                    target = clicked_state
                    self._transition_source = None
                    self._selected_state = None
                    # Ask for label via callback
                    label = None
                    if self._transition_dialog_callback:
                        label = self._transition_dialog_callback(source, target)
                    if label is not None and label.strip():
                        self.transitions.append({
                            'from': source, 'to': target, 'label': label.strip()
                        })
                        self._fire_change()
                    self._redraw()
            else:
                self._transition_source = None
                self._selected_state = None
                self._redraw()

        elif self._mode == 'set_initial':
            if clicked_state:
                # Clear any existing initial
                for data in self.states.values():
                    data['is_initial'] = False
                self.states[clicked_state]['is_initial'] = True
                self._redraw()
                self._fire_change()

        elif self._mode == 'set_accept':
            if clicked_state:
                if self.automaton_type == 'TM':
                    # TM: exclusive accept — clear all, set this one, rename to q_accept
                    for name in list(self.states.keys()):
                        self.states[name]['is_accept'] = False
                    self.states[clicked_state]['is_accept'] = True
                    if clicked_state != 'q_accept':
                        if 'q_accept' in self.states:
                            self._rename_state('q_accept', self._next_available_state_name())
                        self._rename_state(clicked_state, 'q_accept')
                else:
                    self.states[clicked_state]['is_accept'] = not self.states[clicked_state]['is_accept']
                self._redraw()
                self._fire_change()

        elif self._mode == 'set_reject':
            if clicked_state:
                if clicked_state in self.reject_states:
                    # Un-mark reject: rename q_reject back to a generic qN
                    self.reject_states.discard(clicked_state)
                    if clicked_state == 'q_reject':
                        self._rename_state('q_reject', self._next_available_state_name())
                else:
                    # Clear old reject state and rename it back if needed
                    for old in list(self.reject_states):
                        self.reject_states.discard(old)
                        if old == 'q_reject':
                            self._rename_state('q_reject', self._next_available_state_name())
                    # Mark new reject and rename to q_reject
                    # (clicked_state may have been renamed by the loop above, find it)
                    target = clicked_state if clicked_state in self.states else next(
                        iter(self.states), clicked_state)
                    self.reject_states.add(target)
                    if target != 'q_reject':
                        if 'q_reject' in self.states:
                            self._rename_state('q_reject', self._next_available_state_name())
                        self._rename_state(target, 'q_reject')
                self._redraw()
                self._fire_change()

        elif self._mode == 'delete':
            if clicked_state:
                # Remove state and all its transitions
                del self.states[clicked_state]
                self.transitions = [
                    t for t in self.transitions
                    if t['from'] != clicked_state and t['to'] != clicked_state
                ]
                self._redraw()
                self._fire_change()
            else:
                # Check for transition click
                t_idx = self._transition_at(x, y)
                if t_idx is not None:
                    self.transitions.pop(t_idx)
                    self._redraw()
                    self._fire_change()

    def _on_drag(self, event):
        if self._mode == 'select' and self._drag_state:
            name = self._drag_state
            ox, oy = self._drag_offset
            wx, wy = self._screen_to_world(event.x, event.y)
            self.states[name]['x'] = wx - ox
            self.states[name]['y'] = wy - oy
            self._redraw()

    def _on_release(self, event):
        if self._drag_state:
            self._drag_state = None
            self._fire_change()

    def _on_motion(self, event):
        old_hover = self._hover_state
        self._hover_state = self._state_at(event.x, event.y)
        if old_hover != self._hover_state:
            self._redraw()

    # ──────────────────────────────────────────────
    # Rendering
    # ──────────────────────────────────────────────

    def _redraw(self):
        self.canvas.delete('all')
        if not self.states:
            cw = self.canvas.winfo_width() or 450
            ch = self.canvas.winfo_height() or 350
            self.canvas.create_text(
                cw / 2, ch / 2,
                text='Usa la barra para agregar estados.\nScroll=zoom, Shift+drag=mover vista.',
                font=('Segoe UI', 10, 'italic'), fill='#999999', justify=tk.CENTER
            )
            return

        # Draw transitions first (behind states)
        self._draw_all_transitions()

        # Draw initial arrow
        for name, data in self.states.items():
            if data['is_initial']:
                self._draw_initial_arrow(name)

        # Draw states on top
        for name, data in self.states.items():
            self._draw_state(name, data)

        # Draw pending transition line
        if self._mode == 'add_transition' and self._transition_source:
            src = self.states[self._transition_source]
            sx, sy = self._world_to_screen(src['x'], src['y'])
            self.canvas.create_line(
                sx, sy,
                self.canvas.winfo_pointerx() - self.canvas.winfo_rootx(),
                self.canvas.winfo_pointery() - self.canvas.winfo_rooty(),
                dash=(4, 4), fill='#999', width=1.5
            )

    def _draw_state(self, name, data):
        x, y = self._world_to_screen(data['x'], data['y'])
        r = self.STATE_RADIUS
        is_accept = data['is_accept']

        # Determine colors
        if name in self._highlighted_states:
            hl_type = self._highlighted_states[name]
            if hl_type == 'accept':
                fill = self.COLORS['accept_highlight_fill']
                border = self.COLORS['accept_highlight_border']
            elif hl_type == 'reject':
                fill = self.COLORS['reject_fill']
                border = self.COLORS['reject_border']
            else:
                fill = self.COLORS['highlight_fill']
                border = self.COLORS['highlight_border']
        elif self._mode == 'delete' and name == self._hover_state:
            fill = self.COLORS['delete_fill']
            border = self.COLORS['reject_border']
        elif name == self._hover_state:
            fill = self.COLORS['hover_fill']
            border = self.COLORS['state_border']
        elif is_accept:
            fill = self.COLORS['accept_fill']
            border = self.COLORS['accept_border']
        elif name in self.reject_states:
            fill = self.COLORS['reject_fill']
            border = self.COLORS['reject_border']
        else:
            fill = self.COLORS['state_fill']
            border = self.COLORS['state_border']

        border_width = 3 if (name == self._selected_state) else 2
        if name == self._selected_state:
            border = self.COLORS['selected_border']

        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill=fill, outline=border, width=border_width)

        if is_accept:
            inner_r = r - 5 * self._zoom
            self.canvas.create_oval(x - inner_r, y - inner_r,
                                    x + inner_r, y + inner_r,
                                    fill=fill, outline=border, width=border_width)

        font_size = max(7, int(11 * self._zoom))
        self.canvas.create_text(x, y, text=name, font=('Consolas', font_size, 'bold'),
                                fill=border)

        # TM: draw X through reject states
        if name in self.reject_states and name not in self._highlighted_states:
            line_offset = r * 0.55
            self.canvas.create_line(x - line_offset, y - line_offset,
                                    x + line_offset, y + line_offset,
                                    fill=self.COLORS['reject_border'], width=2)
            self.canvas.create_line(x - line_offset, y + line_offset,
                                    x + line_offset, y - line_offset,
                                    fill=self.COLORS['reject_border'], width=2)

    def _draw_initial_arrow(self, state_name):
        data = self.states[state_name]
        x, y = self._world_to_screen(data['x'], data['y'])
        r = self.STATE_RADIUS
        arrow_len = 35 * self._zoom
        start_x = x - r - arrow_len
        self.canvas.create_line(start_x, y, x - r, y,
                                arrow=tk.LAST, fill=self.COLORS['initial_arrow'],
                                width=2, arrowshape=(10, 12, 5))

    def _draw_all_transitions(self):
        # Group transitions by (from, to) to detect bidirectional pairs
        pair_set = set()
        for t in self.transitions:
            pair_set.add((t['from'], t['to']))

        # Group labels for same (from, to)
        grouped = {}
        for t in self.transitions:
            key = (t['from'], t['to'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(t['label'])

        for (from_s, to_s), labels in grouped.items():
            if from_s not in self.states or to_s not in self.states:
                continue
            combined_label = ', '.join(labels) if len(labels[0]) <= 3 else '\n'.join(labels)
            if from_s == to_s:
                self._draw_self_loop(from_s, combined_label)
            else:
                has_reverse = (to_s, from_s) in pair_set
                self._draw_arrow(from_s, to_s, combined_label, curve=has_reverse)

    def _draw_arrow(self, from_state, to_state, label, curve=False):
        s = self.states[from_state]
        e = self.states[to_state]
        x1, y1 = self._world_to_screen(s['x'], s['y'])
        x2, y2 = self._world_to_screen(e['x'], e['y'])
        r = self.STATE_RADIUS

        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            return

        ndx, ndy = dx / dist, dy / dist

        if curve:
            offset = 12
            px, py = -ndy * offset, ndx * offset

            sx = x1 + ndx * r + px
            sy = y1 + ndy * r + py
            ex = x2 - ndx * r + px
            ey = y2 - ndy * r + py

            mx = (sx + ex) / 2 + px * 2
            my = (sy + ey) / 2 + py * 2

            points = [sx, sy, mx, my, ex, ey]
            self.canvas.create_line(*points, smooth=True,
                                    arrow=tk.LAST, fill=self.COLORS['transition'],
                                    width=1.5, arrowshape=(8, 10, 4))
            lx, ly = mx, my - 10
        else:
            sx = x1 + ndx * r
            sy = y1 + ndy * r
            ex = x2 - ndx * r
            ey = y2 - ndy * r

            self.canvas.create_line(sx, sy, ex, ey,
                                    arrow=tk.LAST, fill=self.COLORS['transition'],
                                    width=1.5, arrowshape=(8, 10, 4))

            mx = (sx + ex) / 2
            my = (sy + ey) / 2
            lx = mx - ndy * 14
            ly = my + ndx * 14

        # Draw label with background
        for line_i, line_text in enumerate(label.split('\n')):
            text_y = ly + line_i * 14
            text_id = self.canvas.create_text(lx, text_y, text=line_text,
                                              font=('Consolas', max(7, int(9 * self._zoom))),
                                              fill=self.COLORS['transition_text'])
            bbox = self.canvas.bbox(text_id)
            if bbox:
                pad = 2
                bg = self.canvas.create_rectangle(bbox[0] - pad, bbox[1] - pad,
                                                  bbox[2] + pad, bbox[3] + pad,
                                                  fill='white', outline='')
                self.canvas.tag_raise(text_id)

    def _draw_self_loop(self, state_name, label):
        data = self.states[state_name]
        x, y = self._world_to_screen(data['x'], data['y'])
        r = self.STATE_RADIUS
        loop_r = 20 * self._zoom

        cx = x
        cy = y - r - loop_r
        self.canvas.create_oval(cx - loop_r, cy - loop_r,
                                cx + loop_r, cy + loop_r,
                                outline=self.COLORS['transition'], width=1.5)

        # Arrowhead
        arrow_x = cx + loop_r * 0.7
        arrow_y = cy + loop_r * 0.7
        self.canvas.create_line(arrow_x - 3, arrow_y - 8,
                                arrow_x, arrow_y,
                                arrow_x + 5, arrow_y - 5,
                                fill=self.COLORS['transition'], width=1.5)

        # Label above loop
        for line_i, line_text in enumerate(label.split('\n')):
            text_y = cy - loop_r - 8 + line_i * 14
            text_id = self.canvas.create_text(cx, text_y, text=line_text,
                                              font=('Consolas', max(7, int(9 * self._zoom))),
                                              fill=self.COLORS['transition_text'])
            bbox = self.canvas.bbox(text_id)
            if bbox:
                pad = 2
                self.canvas.create_rectangle(bbox[0] - pad, bbox[1] - pad,
                                             bbox[2] + pad, bbox[3] + pad,
                                             fill='white', outline='')
                self.canvas.tag_raise(text_id)

    # ──────────────────────────────────────────────
    # Legacy compatibility: render_automaton
    # ──────────────────────────────────────────────

    def render_automaton(self, states, initial_state, accept_states,
                         transition_labels, highlighted=None, highlight_type='normal'):
        """Legacy method: load and render an automaton from core model data."""
        self.load_from_model(states, initial_state, accept_states, transition_labels)
        if highlighted:
            self.highlight_states(highlighted, highlight_type)
