"""Pushdown Automaton (PDA) model."""


class PDA:
    def __init__(self):
        self.states = []
        self.input_alphabet = []
        self.stack_alphabet = []
        self.transitions = {}  # (state, input_symbol, stack_top) -> list of (new_state, stack_push)
        self.initial_state = None
        self.initial_stack_symbol = 'Z'
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
                    errors.append(f"Transición PDA inválida (se esperan 3 valores: estado, entrada, tope_pila): {line}")
                    continue
                from_state, input_sym, stack_top = parts
                right_parts = [p.strip() for p in right.split(',', 1)]
                if len(right_parts) != 2:
                    errors.append(f"Transición PDA inválida (se esperan 2 valores: estado, push_pila): {line}")
                    continue
                to_state, stack_push = right_parts

                # Normalize epsilon
                if input_sym in ('ε', 'eps', 'epsilon', ''):
                    input_sym = 'ε'
                if stack_push in ('ε', 'eps', 'epsilon'):
                    stack_push = 'ε'

                if from_state not in pda.states:
                    errors.append(f"Estado origen '{from_state}' no está en los estados")
                if to_state not in pda.states:
                    errors.append(f"Estado destino '{to_state}' no está en los estados")

                key = (from_state, input_sym, stack_top)
                if key not in pda.transitions:
                    pda.transitions[key] = []
                pda.transitions[key].append((to_state, stack_push))

        if not pda.states:
            errors.append("No se definieron estados")
        if pda.initial_state is None:
            errors.append("No se definió estado inicial")
        elif pda.initial_state not in pda.states:
            errors.append(f"Estado inicial '{pda.initial_state}' no está en los estados")

        if errors:
            return None, errors
        return pda, []

    def test(self, input_string, max_steps=1000):
        """Test if string is accepted using BFS.
        Returns (accepted, trace, message).
        trace is a list of (state, remaining_input, stack) for the accepting path.
        """
        if self.initial_state is None:
            return False, [], "No hay estado inicial"

        initial_stack = [self.initial_stack_symbol]
        # BFS: (state, input_pos, stack, path)
        queue = [(self.initial_state, 0, list(initial_stack),
                  [(self.initial_state, input_string, self.initial_stack_symbol)])]
        visited = set()
        steps = 0

        while queue and steps < max_steps:
            steps += 1
            state, pos, stack, path = queue.pop(0)

            # Create a hashable version of state for cycle detection
            stack_tuple = tuple(stack[:10])  # Limit stack depth for visited check
            visit_key = (state, pos, stack_tuple)
            if visit_key in visited:
                continue
            visited.add(visit_key)

            remaining = input_string[pos:]

            # Check acceptance
            if pos == len(input_string):
                if self.accept_by == 'state' and state in self.accept_states:
                    return True, path, "ACEPTADA (por estado final)"
                if self.accept_by == 'empty_stack' and len(stack) == 0:
                    return True, path, "ACEPTADA (por pila vacía)"

            stack_top = stack[-1] if stack else None

            # Try transitions reading input
            if pos < len(input_string):
                symbol = input_string[pos]
                if stack_top:
                    key = (state, symbol, stack_top)
                    for to_state, stack_push in self.transitions.get(key, []):
                        new_stack = list(stack[:-1])  # Pop
                        if stack_push != 'ε':
                            # Push in reverse order so first char is on top
                            for ch in reversed(stack_push):
                                new_stack.append(ch)
                        stack_str = ''.join(reversed(new_stack)) if new_stack else '∅'
                        new_path = path + [(to_state, input_string[pos + 1:], stack_str)]
                        queue.append((to_state, pos + 1, new_stack, new_path))

            # Try epsilon transitions
            if stack_top:
                key = (state, 'ε', stack_top)
                for to_state, stack_push in self.transitions.get(key, []):
                    new_stack = list(stack[:-1])  # Pop
                    if stack_push != 'ε':
                        for ch in reversed(stack_push):
                            new_stack.append(ch)
                    stack_str = ''.join(reversed(new_stack)) if new_stack else '∅'
                    new_path = path + [(to_state, remaining, stack_str)]
                    queue.append((to_state, pos, new_stack, new_path))

        if steps >= max_steps:
            return False, [], f"Se alcanzó el límite de {max_steps} pasos (posible bucle infinito)"
        return False, [], "RECHAZADA (no se encontró camino de aceptación)"

    def get_transition_labels(self):
        """Group transitions for display: (from, to) -> [labels]."""
        labels = {}
        for (from_s, input_sym, stack_top), targets in self.transitions.items():
            for to_s, stack_push in targets:
                key = (from_s, to_s)
                label = f"{input_sym}, {stack_top}/{stack_push}"
                if key not in labels:
                    labels[key] = []
                labels[key].append(label)
        return {k: '\n'.join(v) for k, v in labels.items()}

    @staticmethod
    def example():
        return """# PDA: Acepta {a^n b^n | n >= 1}
States: q0, q1, q2
Input Alphabet: a, b
Stack Alphabet: A, Z
Initial: q0
Initial Stack: Z
Accept: q2
Transitions:
q0, a, Z -> q0, AZ
q0, a, A -> q0, AA
q0, b, A -> q1, ε
q1, b, A -> q1, ε
q1, ε, Z -> q2, Z"""

    @staticmethod
    def example2():
        return """# PDA: Acepta {w w^R | w en {a,b}*} (palíndromos pares)
States: q0, q1, q2
Input Alphabet: a, b
Stack Alphabet: A, B, Z
Initial: q0
Initial Stack: Z
Accept: q2
Transitions:
q0, a, Z -> q0, AZ
q0, b, Z -> q0, BZ
q0, a, A -> q0, AA
q0, a, B -> q0, AB
q0, b, A -> q0, BA
q0, b, B -> q0, BB
q0, ε, A -> q1, A
q0, ε, B -> q1, B
q0, ε, Z -> q1, Z
q1, a, A -> q1, ε
q1, b, B -> q1, ε
q1, ε, Z -> q2, Z"""
