"""Pushdown Automaton (PDA) model.

Transition semantics (textbook style):
    (state, input, pop) -> (new_state, push)
    - input = ε: don't read from input
    - pop = ε: don't pop anything from stack
    - pop = X: require X on top, pop it
    - push = ε: don't push anything
    - push = X: push X onto stack
    - push = XY: push Y first, then X (X ends on top)
"""


class PDA:
    def __init__(self):
        self.states = []
        self.input_alphabet = []
        self.stack_alphabet = []
        self.transitions = {}  # (state, input, pop) -> list of (new_state, push)
        self.initial_state = None
        self.initial_stack_symbol = ''  # Empty by default - user pushes via transitions
        self.accept_states = set()
        self.accept_by = 'state'  # 'state' or 'empty_stack'

    @staticmethod
    def parse(text):
        """Parse text definition into a PDA. Returns (PDA, errors)."""
        pda = PDA()
        lines = text.strip().split('\n')
        errors = []

        for line in lines:
            line = line.split('#')[0].strip()
            if not line:
                continue

            lower = line.lower()
            if lower.startswith('states:') or lower.startswith('estados:'):
                pda.states = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('input alphabet:') or lower.startswith('alfabeto entrada:') or lower.startswith('alfabeto de entrada:'):
                pda.input_alphabet = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('stack alphabet:') or lower.startswith('alfabeto pila:') or lower.startswith('alfabeto de pila:'):
                pda.stack_alphabet = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('initial:') or lower.startswith('inicial:'):
                pda.initial_state = line.split(':', 1)[1].strip()
            elif lower.startswith('initial stack:') or lower.startswith('pila inicial:'):
                pda.initial_stack_symbol = line.split(':', 1)[1].strip()
            elif lower.startswith('accept:') or lower.startswith('aceptacion:') or lower.startswith('aceptación:'):
                pda.accept_states = {s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()}
            elif lower.startswith('accept by:') or lower.startswith('aceptar por:'):
                val = line.split(':', 1)[1].strip().lower()
                if val in ('empty stack', 'pila vacía', 'pila vacia', 'empty'):
                    pda.accept_by = 'empty_stack'
                else:
                    pda.accept_by = 'state'
            elif lower.startswith('transition') or lower.startswith('transicion') or lower.startswith('transición'):
                continue
            elif '->' in line:
                left, right = line.split('->', 1)
                parts = [p.strip() for p in left.split(',')]
                if len(parts) != 3:
                    errors.append(f"Transicion PDA invalida (estado, entrada, pop): {line}")
                    continue
                from_state, input_sym, pop_sym = parts
                right_parts = [p.strip() for p in right.split(',', 1)]
                if len(right_parts) != 2:
                    errors.append(f"Transicion PDA invalida (estado, push): {line}")
                    continue
                to_state, push_sym = right_parts

                # Normalize epsilon
                if input_sym in ('ε', 'eps', 'epsilon', ''):
                    input_sym = 'ε'
                if pop_sym in ('ε', 'eps', 'epsilon', ''):
                    pop_sym = 'ε'
                if push_sym in ('ε', 'eps', 'epsilon', ''):
                    push_sym = 'ε'

                if from_state not in pda.states:
                    errors.append(f"Estado origen '{from_state}' no esta en los estados")
                if to_state not in pda.states:
                    errors.append(f"Estado destino '{to_state}' no esta en los estados")

                key = (from_state, input_sym, pop_sym)
                if key not in pda.transitions:
                    pda.transitions[key] = []
                pda.transitions[key].append((to_state, push_sym))

        if not pda.states:
            errors.append("No se definieron estados")
        if pda.initial_state is None:
            errors.append("No se definio estado inicial")
        elif pda.initial_state not in pda.states:
            errors.append(f"Estado inicial '{pda.initial_state}' no esta en los estados")

        if errors:
            return None, errors
        return pda, []

    def test(self, input_string, max_steps=2000):
        """Test if string is accepted using BFS.

        Transition semantics:
        - pop = ε: don't check or pop stack, just push
        - pop = X: require X on top of stack, pop it, then push
        - push = ε: don't push anything
        - push = ABC: push C first, then B, then A (A ends on top)

        Returns (accepted, trace, message).
        """
        if self.initial_state is None:
            return False, [], "No hay estado inicial"

        initial_stack = [self.initial_stack_symbol] if self.initial_stack_symbol else []
        initial_stack_display = stack_str(initial_stack) if initial_stack else '\u2205'
        queue = [(self.initial_state, 0, list(initial_stack),
                  [(self.initial_state, input_string, initial_stack_display)])]
        visited = set()
        steps = 0

        def stack_str(stack):
            return ''.join(reversed(stack)) if stack else '∅'

        def try_transition(state, pos, stack, path, input_sym, advance):
            """Try all transitions for (state, input_sym, pop) with all possible pop values."""
            results = []
            remaining = input_string[pos + advance:] if advance else input_string[pos:]

            # Try pop = ε (don't pop, just push)
            key_eps = (state, input_sym, 'ε')
            for to_state, push_sym in self.transitions.get(key_eps, []):
                new_stack = list(stack)  # No pop
                if push_sym != 'ε':
                    for ch in reversed(push_sym):
                        new_stack.append(ch)
                new_path = path + [(to_state, remaining, stack_str(new_stack))]
                results.append((to_state, pos + advance, new_stack, new_path))

            # Try pop = specific symbol (check top, pop it, then push)
            if stack:
                top = stack[-1]
                key_top = (state, input_sym, top)
                for to_state, push_sym in self.transitions.get(key_top, []):
                    new_stack = list(stack[:-1])  # Pop
                    if push_sym != 'ε':
                        for ch in reversed(push_sym):
                            new_stack.append(ch)
                    new_path = path + [(to_state, remaining, stack_str(new_stack))]
                    results.append((to_state, pos + advance, new_stack, new_path))

            return results

        # Track best path (most input consumed) for rejection info
        best_path = []
        best_pos = -1

        while queue and steps < max_steps:
            steps += 1
            state, pos, stack, path = queue.pop(0)

            # Cycle detection
            stack_tuple = tuple(stack[:15])
            visit_key = (state, pos, stack_tuple)
            if visit_key in visited:
                continue
            visited.add(visit_key)

            # Track the path that consumed the most input
            if pos > best_pos or (pos == best_pos and len(path) > len(best_path)):
                best_pos = pos
                best_path = path

            # Check acceptance
            if pos == len(input_string):
                if self.accept_by == 'state' and state in self.accept_states:
                    return True, path, "ACEPTADA (por estado final)"
                if self.accept_by == 'empty_stack' and len(stack) == 0:
                    return True, path, "ACEPTADA (por pila vacia)"

            # Try transitions reading input symbol
            if pos < len(input_string):
                symbol = input_string[pos]
                for result in try_transition(state, pos, stack, path, symbol, advance=1):
                    queue.append(result)

            # Try epsilon transitions (don't read input)
            for result in try_transition(state, pos, stack, path, 'ε', advance=0):
                queue.append(result)

        if steps >= max_steps:
            return False, best_path, f"Se alcanzo el limite de {max_steps} pasos (posible bucle infinito)"

        # Build rejection reason
        if best_path:
            last_state, last_remaining, last_stack = best_path[-1]
            consumed = len(input_string) - len(last_remaining) if last_remaining else len(input_string)
            if consumed < len(input_string):
                reason = (f"RECHAZADA - Se atasco en estado '{last_state}' "
                          f"tras leer {consumed}/{len(input_string)} simbolos. "
                          f"Pila: {last_stack}")
            elif self.accept_by == 'state':
                reason = (f"RECHAZADA - Leyo toda la entrada pero termino en "
                          f"estado '{last_state}' (no es de aceptacion). Pila: {last_stack}")
            else:
                reason = (f"RECHAZADA - Leyo toda la entrada pero la pila "
                          f"no quedo vacia ({last_stack})")
        else:
            reason = "RECHAZADA (no se encontro camino de aceptacion)"

        return False, best_path, reason

    def get_transition_labels(self):
        """Group transitions for display: (from, to) -> [labels].
        Label format: 'input, pop → push' (textbook style).
        """
        labels = {}
        for (from_s, input_sym, pop_sym), targets in self.transitions.items():
            for to_s, push_sym in targets:
                key = (from_s, to_s)
                label = f"{input_sym}, {pop_sym} \u2192 {push_sym}"
                if key not in labels:
                    labels[key] = []
                labels[key].append(label)
        return {k: '\n'.join(v) for k, v in labels.items()}

    def get_formal_definition(self):
        """Return the formal 6-tuple string."""
        q_set = '{' + ', '.join(self.states) + '}'
        sigma = '{' + ', '.join(self.input_alphabet) + '}'
        gamma = '{' + ', '.join(self.stack_alphabet) + '}'
        f_set = '{' + ', '.join(sorted(self.accept_states)) + '}'
        q0 = self.initial_state or '?'
        accept_note = ('por estado final' if self.accept_by == 'state'
                       else 'por pila vac\u00eda')
        return (
            f"M = (Q, \u03a3, \u0393, \u03b4, q\u2080, F)  [{accept_note}]\n"
            f"  Q = {q_set}\n"
            f"  \u03a3 = {sigma}\n"
            f"  \u0393 = {gamma}\n"
            f"  q\u2080 = {q0}\n"
            f"  F = {f_set}"
        )

    def get_transition_table(self):
        """Return \u03b4 as rows: (from, input, pop, to, push)."""
        rows = []
        for (from_s, input_sym, pop_sym), targets in sorted(self.transitions.items()):
            for to_s, push_sym in targets:
                rows.append((from_s, input_sym, pop_sym, to_s, push_sym))
        return rows

    @staticmethod
    def example():
        return """# PDA: Acepta {0^n 1^n | n >= 1}
# Formato: estado, entrada, pop -> estado, push
# Pila vacia al inicio, se pushea $ via transicion
States: q1, q2, q3, q4
Input Alphabet: 0, 1
Stack Alphabet: $, ×
Initial: q1
Accept: q1, q4
Transitions:
q1, ε, ε -> q2, $
q2, 0, ε -> q2, ×
q2, 1, × -> q3, ε
q3, 1, × -> q3, ε
q3, ε, $ -> q4, ε"""

    @staticmethod
    def example2():
        return """# PDA: Acepta {a^n b^n | n >= 0} (incluye cadena vacia)
# Pila vacia al inicio, se pushea $ via transicion
States: q0, q1, q2
Input Alphabet: a, b
Stack Alphabet: $, A
Initial: q0
Accept: q0, q2
Transitions:
q0, ε, ε -> q1, $
q1, a, ε -> q1, A
q1, b, A -> q2, ε
q2, b, A -> q2, ε
q2, ε, $ -> q2, ε"""
