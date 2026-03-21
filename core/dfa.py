"""Deterministic Finite Automaton (DFA) model."""


class DFA:
    def __init__(self):
        self.states = []
        self.alphabet = []
        self.transitions = {}  # (state, symbol) -> state
        self.initial_state = None
        self.accept_states = set()

    @staticmethod
    def parse(text):
        """Parse text definition into a DFA. Returns (DFA, errors)."""
        dfa = DFA()
        lines = text.strip().split('\n')
        in_transitions = False
        errors = []

        for line in lines:
            line = line.split('#')[0].strip()
            if not line:
                continue

            lower = line.lower()
            if lower.startswith('states:') or lower.startswith('estados:'):
                dfa.states = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('alphabet:') or lower.startswith('alfabeto:'):
                dfa.alphabet = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('initial:') or lower.startswith('inicial:'):
                dfa.initial_state = line.split(':', 1)[1].strip()
            elif lower.startswith('accept:') or lower.startswith('aceptacion:') or lower.startswith('aceptación:'):
                dfa.accept_states = {s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()}
            elif lower.startswith('transition') or lower.startswith('transicion') or lower.startswith('transición'):
                in_transitions = True
            elif '->' in line:
                in_transitions = True
                left, right = line.split('->', 1)
                parts = [p.strip() for p in left.split(',')]
                if len(parts) != 2:
                    errors.append(f"Transición inválida (se esperan 2 valores antes de ->): {line}")
                    continue
                from_state, symbol = parts[0], parts[1]
                to_state = right.strip()
                if from_state not in dfa.states:
                    errors.append(f"Estado origen '{from_state}' no está en los estados definidos")
                if to_state not in dfa.states:
                    errors.append(f"Estado destino '{to_state}' no está en los estados definidos")
                if symbol and symbol not in dfa.alphabet:
                    dfa.alphabet.append(symbol)
                dfa.transitions[(from_state, symbol)] = to_state

        if not dfa.states:
            errors.append("No se definieron estados")
        if dfa.initial_state is None:
            errors.append("No se definió estado inicial")
        elif dfa.initial_state not in dfa.states:
            errors.append(f"Estado inicial '{dfa.initial_state}' no está en los estados")
        for s in dfa.accept_states:
            if s not in dfa.states:
                errors.append(f"Estado de aceptación '{s}' no está en los estados")

        if errors:
            return None, errors
        return dfa, []

    def test(self, input_string):
        """Test if string is accepted.
        Returns (accepted: bool, path: list of (state, symbol_read), message: str).
        """
        if self.initial_state is None:
            return False, [], "No hay estado inicial definido"

        current = self.initial_state
        path = [(current, '')]

        for symbol in input_string:
            if symbol not in self.alphabet:
                return False, path, f"Símbolo '{symbol}' no está en el alfabeto {self.alphabet}"
            key = (current, symbol)
            if key not in self.transitions:
                return False, path, f"No hay transición desde '{current}' con símbolo '{symbol}'"
            current = self.transitions[key]
            path.append((current, symbol))

        accepted = current in self.accept_states
        msg = "ACEPTADA" if accepted else f"RECHAZADA (estado final '{current}' no es de aceptación)"
        return accepted, path, msg

    def get_transition_labels(self):
        """Group transitions for display: (from, to) -> [symbols]."""
        labels = {}
        for (from_s, symbol), to_s in self.transitions.items():
            key = (from_s, to_s)
            if key not in labels:
                labels[key] = []
            labels[key].append(symbol)
        return {k: ', '.join(sorted(v)) for k, v in labels.items()}

    @staticmethod
    def example():
        return """# DFA: Cadenas binarias divisibles por 3
States: q0, q1, q2
Alphabet: 0, 1
Initial: q0
Accept: q0
Transitions:
q0, 0 -> q0
q0, 1 -> q1
q1, 0 -> q2
q1, 1 -> q0
q2, 0 -> q1
q2, 1 -> q2"""

    @staticmethod
    def example2():
        return """# DFA: Cadenas sobre {a,b} que contienen "aba"
States: q0, q1, q2, q3
Alphabet: a, b
Initial: q0
Accept: q3
Transitions:
q0, a -> q1
q0, b -> q0
q1, a -> q1
q1, b -> q2
q2, a -> q3
q2, b -> q0
q3, a -> q3
q3, b -> q3"""
