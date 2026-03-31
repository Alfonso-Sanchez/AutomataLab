"""Non-deterministic Finite Automaton (NFA) model."""


class NFA:
    def __init__(self):
        self.states = []
        self.alphabet = []
        self.transitions = {}  # (state, symbol) -> set of states
        self.initial_state = None
        self.accept_states = set()

    @staticmethod
    def parse(text):
        """Parse text definition into an NFA. Returns (NFA, errors)."""
        nfa = NFA()
        lines = text.strip().split('\n')
        errors = []

        for line in lines:
            line = line.split('#')[0].strip()
            if not line:
                continue

            lower = line.lower()
            if lower.startswith('states:') or lower.startswith('estados:'):
                nfa.states = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('alphabet:') or lower.startswith('alfabeto:'):
                nfa.alphabet = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('initial:') or lower.startswith('inicial:'):
                nfa.initial_state = line.split(':', 1)[1].strip()
            elif lower.startswith('accept:') or lower.startswith('aceptacion:') or lower.startswith('aceptación:'):
                nfa.accept_states = {s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()}
            elif lower.startswith('transition') or lower.startswith('transicion') or lower.startswith('transición'):
                continue
            elif '->' in line:
                left, right = line.split('->', 1)
                parts = [p.strip() for p in left.split(',')]
                if len(parts) != 2:
                    errors.append(f"Transición inválida: {line}")
                    continue
                from_state = parts[0]
                symbol = parts[1]
                # Normalize epsilon
                if symbol in ('ε', 'eps', 'epsilon', 'épsilon', ''):
                    symbol = 'ε'
                to_states = {s.strip() for s in right.split(',') if s.strip()}
                for ts in to_states:
                    if ts not in nfa.states:
                        errors.append(f"Estado destino '{ts}' no está en los estados")
                if from_state not in nfa.states:
                    errors.append(f"Estado origen '{from_state}' no está en los estados")
                if symbol != 'ε' and symbol not in nfa.alphabet:
                    nfa.alphabet.append(symbol)

                key = (from_state, symbol)
                if key not in nfa.transitions:
                    nfa.transitions[key] = set()
                nfa.transitions[key].update(to_states)

        if not nfa.states:
            errors.append("No se definieron estados")
        if nfa.initial_state is None:
            errors.append("No se definió estado inicial")
        elif nfa.initial_state not in nfa.states:
            errors.append(f"Estado inicial '{nfa.initial_state}' no está en los estados")
        for s in nfa.accept_states:
            if s not in nfa.states:
                errors.append(f"Estado de aceptación '{s}' no está en los estados")

        if errors:
            return None, errors
        return nfa, []

    def epsilon_closure(self, states):
        """Compute epsilon closure of a set of states."""
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            eps_targets = self.transitions.get((state, 'ε'), set())
            for t in eps_targets:
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return closure

    def test(self, input_string):
        """Test if string is accepted.
        Returns (accepted, trace: list of (set_of_states, symbol), message).
        """
        if self.initial_state is None:
            return False, [], "No hay estado inicial definido"

        current_states = self.epsilon_closure({self.initial_state})
        trace = [(frozenset(current_states), '')]

        for symbol in input_string:
            if symbol not in self.alphabet:
                return False, trace, f"Símbolo '{symbol}' no está en el alfabeto"
            next_states = set()
            for state in current_states:
                targets = self.transitions.get((state, symbol), set())
                next_states.update(targets)
            current_states = self.epsilon_closure(next_states)
            trace.append((frozenset(current_states), symbol))

            if not current_states:
                return False, trace, "No hay estados alcanzables (cadena muerta)"

        accepted = bool(current_states & self.accept_states)
        msg = "ACEPTADA" if accepted else "RECHAZADA (ningún estado final es de aceptación)"
        return accepted, trace, msg

    def get_transition_labels(self):
        """Group transitions for display: (from, to) -> [symbols]."""
        labels = {}
        for (from_s, symbol), to_states in self.transitions.items():
            for to_s in to_states:
                key = (from_s, to_s)
                if key not in labels:
                    labels[key] = []
                labels[key].append(symbol)
        return {k: ', '.join(sorted(v)) for k, v in labels.items()}

    def get_formal_definition(self):
        """Return the formal 5-tuple string."""
        q_set = '{' + ', '.join(self.states) + '}'
        has_eps = any(s == '\u03b5' for (_, s) in self.transitions.keys())
        sigma_base = ', '.join(self.alphabet)
        sigma = '{' + sigma_base + (', \u03b5' if has_eps else '') + '}'
        f_set = '{' + ', '.join(sorted(self.accept_states)) + '}'
        q0 = self.initial_state or '?'
        return (
            f"M = (Q, \u03a3, \u03b4, q\u2080, F)\n"
            f"  Q = {q_set}\n"
            f"  \u03a3 = {sigma}\n"
            f"  q\u2080 = {q0}\n"
            f"  F = {f_set}"
        )

    def get_transition_table(self):
        """Return \u03b4 as a list of rows: (from_state, symbol, frozenset_of_to_states)."""
        rows = []
        for (from_s, symbol), to_states in sorted(self.transitions.items()):
            rows.append((from_s, symbol, frozenset(to_states)))
        return rows

    def get_epsilon_closures(self):
        """Return epsilon closure for each state that has one."""
        closures = {}
        for state in self.states:
            c = self.epsilon_closure({state})
            if c != {state}:
                closures[state] = c
        return closures

    @staticmethod
    def example():
        return """# NFA: Cadenas sobre {a,b} que terminan en "ab"
States: q0, q1, q2
Alphabet: a, b
Initial: q0
Accept: q2
Transitions:
q0, a -> q0, q1
q0, b -> q0
q1, b -> q2"""

    @staticmethod
    def example2():
        return """# NFA con transiciones epsilon
# Acepta: cadenas con al menos una 'a' o al menos una 'b'
States: q0, q1, q2, q3, q4
Alphabet: a, b
Initial: q0
Accept: q2, q4
Transitions:
q0, ε -> q1, q3
q1, a -> q2
q2, a -> q2
q3, b -> q4
q4, b -> q4"""
