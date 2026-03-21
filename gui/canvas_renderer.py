"""Interactive canvas-based automata builder using tkinter Canvas."""

import math
import tkinter as tk
from tkinter import ttk


class AutomataCanvas(ttk.Frame):
    """Composite widget: toolbar + interactive canvas for building automata visually."""

    STATE_RADIUS = 28
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
        'delete': 'Eliminar',
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self._on_change_callback = None
        self._transition_dialog_callback = None

        # --- Data model ---
        self.states = {}       # name -> {'x': float, 'y': float, 'is_initial': bool, 'is_accept': bool}
        self.transitions = []  # [{'from': str, 'to': str, 'label': str}]

        # --- Interaction state ---
        self._mode = 'select'
        self._next_state_id = 0
        self._drag_state = None
        self._drag_offset = (0, 0)
        self._transition_source = None  # source state name for transition mode
        self._hover_state = None
        self._selected_state = None
        self._highlighted_states = {}  # name -> highlight_type ('normal', 'accept', 'reject')

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

    # ──────────────────────────────────────────────
    # Toolbar
    # ──────────────────────────────────────────────

    def _build_toolbar(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill=tk.X, padx=2, pady=(2, 0))

        self._mode_buttons = {}
        modes_config = [
            ('add_state', '\u2795 Estado'),
            ('add_transition', '\u27a1 Transicion'),
            ('set_initial', '\U0001f3c1 Inicial'),
            ('set_accept', '\u2713 Aceptacion'),
            ('delete', '\U0001f5d1 Eliminar'),
        ]
        for mode_key, label in modes_config:
            btn = ttk.Button(self.toolbar, text=label,
                             command=lambda m=mode_key: self.set_mode(m))
            btn.pack(side=tk.LEFT, padx=1)
            self._mode_buttons[mode_key] = btn

        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        self._btn_clear = ttk.Button(self.toolbar, text='\U0001f9f9 Limpiar',
                                     command=self.clear_all)
        self._btn_clear.pack(side=tk.LEFT, padx=1)

        # Mode indicator label
        self._mode_label = ttk.Label(self.toolbar, text='Modo: Seleccionar',
                                     font=('Segoe UI', 8, 'italic'))
        self._mode_label.pack(side=tk.RIGHT, padx=6)

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
        self._next_state_id = 0

        if not states:
            self._redraw()
            return

        # Layout in circle
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
            # Track next auto-id
            if name.startswith('q'):
                try:
                    num = int(name[1:])
                    self._next_state_id = max(self._next_state_id, num + 1)
                except ValueError:
                    pass

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
        self._next_state_id = 0
        self._drag_state = None
        self._transition_source = None
        self._hover_state = None
        self._selected_state = None
        self._highlighted_states = {}
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

    # ──────────────────────────────────────────────
    # Event handlers
    # ──────────────────────────────────────────────

    def _fire_change(self):
        if self._on_change_callback:
            self._on_change_callback()

    def _state_at(self, x, y):
        """Return state name at canvas position, or None."""
        r = self.STATE_RADIUS
        for name, data in self.states.items():
            dx = x - data['x']
            dy = y - data['y']
            if dx * dx + dy * dy <= (r + 4) ** 2:
                return name
        return None

    def _transition_at(self, x, y):
        """Return index of transition near position, or None."""
        threshold = 12
        for i, t in enumerate(self.transitions):
            if t['from'] not in self.states or t['to'] not in self.states:
                continue
            s = self.states[t['from']]
            e = self.states[t['to']]

            if t['from'] == t['to']:
                # Self-loop: check if near the loop circle above
                loop_cx = s['x']
                loop_cy = s['y'] - self.STATE_RADIUS - 20
                dist = math.sqrt((x - loop_cx) ** 2 + (y - loop_cy) ** 2)
                if abs(dist - 20) < threshold:
                    return i
            else:
                # Check distance to line segment
                dist = self._point_to_segment_dist(x, y, s['x'], s['y'], e['x'], e['y'])
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
                self._drag_offset = (x - data['x'], y - data['y'])
                self._selected_state = clicked_state
            else:
                self._selected_state = None
            self._redraw()

        elif self._mode == 'add_state':
            if not clicked_state:
                name = f'q{self._next_state_id}'
                self._next_state_id += 1
                is_initial = len(self.states) == 0  # first state is initial by default
                self.states[name] = {
                    'x': x, 'y': y,
                    'is_initial': is_initial,
                    'is_accept': False,
                }
                # If this is initial, make sure no other state is initial
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
                self.states[clicked_state]['is_accept'] = not self.states[clicked_state]['is_accept']
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
            self.states[name]['x'] = event.x - ox
            self.states[name]['y'] = event.y - oy
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
            self.canvas.create_text(
                self.canvas.winfo_width() / 2 or 225,
                self.canvas.winfo_height() / 2 or 175,
                text='Usa la barra de herramientas para agregar estados y transiciones',
                font=('Segoe UI', 10, 'italic'), fill='#999999'
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
            # Draw a dashed line from source to cursor
            self.canvas.create_line(
                src['x'], src['y'],
                self.canvas.winfo_pointerx() - self.canvas.winfo_rootx(),
                self.canvas.winfo_pointery() - self.canvas.winfo_rooty(),
                dash=(4, 4), fill='#999', width=1.5
            )

    def _draw_state(self, name, data):
        x, y = data['x'], data['y']
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
        else:
            fill = self.COLORS['state_fill']
            border = self.COLORS['state_border']

        border_width = 3 if (name == self._selected_state) else 2
        if name == self._selected_state:
            border = self.COLORS['selected_border']

        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill=fill, outline=border, width=border_width)

        if is_accept:
            inner_r = r - 5
            self.canvas.create_oval(x - inner_r, y - inner_r,
                                    x + inner_r, y + inner_r,
                                    fill=fill, outline=border, width=border_width)

        self.canvas.create_text(x, y, text=name, font=('Consolas', 11, 'bold'),
                                fill=border)

    def _draw_initial_arrow(self, state_name):
        data = self.states[state_name]
        x, y = data['x'], data['y']
        r = self.STATE_RADIUS
        start_x = x - r - 35
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
        x1, y1 = s['x'], s['y']
        x2, y2 = e['x'], e['y']
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
                                              font=('Consolas', 9),
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
        x, y = data['x'], data['y']
        r = self.STATE_RADIUS
        loop_r = 20

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
                                              font=('Consolas', 9),
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
