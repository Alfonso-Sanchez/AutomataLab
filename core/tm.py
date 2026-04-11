"""Turing Machine (TM) model.

Definition: (Q, Sigma, Gamma, delta, q0, q_accept, q_reject)
- Q: finite set of states
- Sigma: input alphabet (no blank symbol)
- Gamma: tape alphabet, where blank in Gamma and Sigma subset Gamma
- delta: Q x Gamma -> Q x Gamma x {L, R}
- q0: start state
- q_accept: accept state (halts immediately)
- q_reject: optional reject state (halts immediately when present)

Transition format: delta(q, a) = (q', b, D)
  Read 'a' in state q -> write 'b', move D (L/R), go to state q'.
  Diagram label: a -> b, D
"""

BLANK = '\u2294'  # ⊔


class TuringMachine:
    def __init__(self):
        self.states = []
        self.input_alphabet = []
        self.tape_alphabet = []
        self.transitions = {}  # (state, read_sym) -> (new_state, write_sym, direction)
        self.initial_state = None
        self.accept_state = None
        self.reject_state = None

    @staticmethod
    def parse(text):
        """Parse text definition into a TM. Returns (TM, errors)."""
        tm = TuringMachine()
        lines = text.strip().split('\n')
        errors = []

        for line in lines:
            # Only treat # as comment if it starts the line (after stripping)
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            line = stripped
            if not line:
                continue

            lower = line.lower()
            if lower.startswith('states:') or lower.startswith('estados:'):
                tm.states = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('input alphabet:') or lower.startswith('alfabeto entrada:'):
                tm.input_alphabet = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('tape alphabet:') or lower.startswith('alfabeto cinta:'):
                tm.tape_alphabet = [s.strip() for s in line.split(':', 1)[1].split(',') if s.strip()]
            elif lower.startswith('initial:') or lower.startswith('inicial:'):
                tm.initial_state = line.split(':', 1)[1].strip()
            elif lower.startswith('accept:') or lower.startswith('aceptacion:'):
                tm.accept_state = line.split(':', 1)[1].strip()
            elif lower.startswith('reject:') or lower.startswith('rechazo:'):
                tm.reject_state = line.split(':', 1)[1].strip()
            elif lower.startswith('transition') or lower.startswith('transicion'):
                continue
            elif '->' in line:
                # Format: state, read -> new_state, write, direction
                left, right = line.split('->', 1)
                left_parts = [p.strip() for p in left.split(',')]
                right_parts = [p.strip() for p in right.split(',')]
                if len(left_parts) != 2:
                    errors.append(f"Transicion TM invalida (estado, leer): {line}")
                    continue
                if len(right_parts) != 3:
                    errors.append(f"Transicion TM invalida (estado, escribir, dir): {line}")
                    continue
                from_state, read_sym = left_parts
                to_state, write_sym, direction = right_parts

                # Normalize blank symbol
                if read_sym in ('_', 'B', 'blank', '\u2294'):
                    read_sym = BLANK
                if write_sym in ('_', 'B', 'blank', '\u2294'):
                    write_sym = BLANK

                direction = direction.upper()
                if direction not in ('L', 'R'):
                    errors.append(f"Direccion invalida '{direction}' (debe ser L o R): {line}")
                    continue

                if from_state not in tm.states:
                    errors.append(f"Estado '{from_state}' no esta en los estados")
                if to_state not in tm.states:
                    errors.append(f"Estado '{to_state}' no esta en los estados")

                key = (from_state, read_sym)
                if key in tm.transitions:
                    errors.append(f"Transicion duplicada para ({from_state}, {read_sym}) - TM es determinista")
                    continue
                tm.transitions[key] = (to_state, write_sym, direction)

        # Auto-add blank to tape alphabet
        if BLANK not in tm.tape_alphabet:
            tm.tape_alphabet.append(BLANK)

        if not tm.states:
            errors.append("No se definieron estados")
        if tm.initial_state is None:
            errors.append("No se definio estado inicial")
        if tm.accept_state is None:
            errors.append("No se definio estado de aceptacion")
        if tm.accept_state and tm.reject_state and tm.accept_state == tm.reject_state:
            errors.append("q_accept y q_reject deben ser diferentes")

        if errors:
            return None, errors
        return tm, []

    def test(self, input_string, max_steps=5000):
        """Run the TM on input.
        Returns (result: str, trace: list of snapshots, message: str).
        result is 'accept', 'reject', or 'loop'.
        Each snapshot: (state, tape_list, head_pos, step_number).
        """
        if self.initial_state is None:
            return 'reject', [], "No hay estado inicial"

        # Initialize tape
        tape = [ch for ch in input_string] if input_string else [BLANK]
        if not tape:
            tape = [BLANK]
        head = 0
        state = self.initial_state

        trace = [(state, list(tape), head, 0)]
        steps = 0
        seen_configs = set()  # For loop detection

        while steps < max_steps:
            # Check halt states
            if state == self.accept_state:
                return 'accept', trace, "ACEPTADA"
            if state == self.reject_state:
                return 'reject', trace, "RECHAZADA"

            # Extend tape if head is at the end
            if head >= len(tape):
                tape.append(BLANK)
            if head < 0:
                tape.insert(0, BLANK)
                head = 0

            read_sym = tape[head]
            key = (state, read_sym)

            if key not in self.transitions:
                return 'reject', trace, f"RECHAZADA (sin transicion para ({state}, {read_sym}))"

            # Loop detection: check if we've seen this exact configuration
            # (state, head position, tape content up to last non-blank)
            tape_trimmed = tuple(tape[:max(head + 1, len(tape))])
            config_key = (state, head, tape_trimmed)
            if config_key in seen_configs:
                return 'loop', trace, (
                    f"BUCLE DETECTADO en paso {steps}: "
                    f"configuracion ({state}, pos={head}) ya fue visitada"
                )
            seen_configs.add(config_key)

            new_state, write_sym, direction = self.transitions[key]
            tape[head] = write_sym
            state = new_state

            if direction == 'R':
                head += 1
            else:  # L
                head -= 1
                if head < 0:
                    tape.insert(0, BLANK)
                    head = 0

            steps += 1

            # Extend tape if needed
            if head >= len(tape):
                tape.append(BLANK)

            trace.append((state, list(tape), head, steps))

        return 'loop', trace, f"POSIBLE BUCLE INFINITO (limite de {max_steps} pasos alcanzado)"

    def step_generator(self, input_string):
        """Generator that yields one configuration at a time.
        Yields (state, tape, head, step, status).
        status: 'running', 'accept', 'reject'.
        """
        tape = [ch for ch in input_string] if input_string else [BLANK]
        if not tape:
            tape = [BLANK]
        head = 0
        state = self.initial_state

        yield (state, list(tape), head, 0, 'running')
        step = 0

        while True:
            if state == self.accept_state:
                yield (state, list(tape), head, step, 'accept')
                return
            if state == self.reject_state:
                yield (state, list(tape), head, step, 'reject')
                return

            if head >= len(tape):
                tape.append(BLANK)

            read_sym = tape[head]
            key = (state, read_sym)

            if key not in self.transitions:
                yield (state, list(tape), head, step, 'reject')
                return

            new_state, write_sym, direction = self.transitions[key]
            tape[head] = write_sym
            state = new_state

            if direction == 'R':
                head += 1
            else:
                head -= 1
                if head < 0:
                    tape.insert(0, BLANK)
                    head = 0

            step += 1
            if head >= len(tape):
                tape.append(BLANK)

            status = 'running'
            if state == self.accept_state:
                status = 'accept'
            elif state == self.reject_state:
                status = 'reject'

            yield (state, list(tape), head, step, status)

            if step > 10000:
                yield (state, list(tape), head, step, 'loop')
                return

    @staticmethod
    def configuration_string(state, tape, head):
        """Build textbook configuration notation: w1...w_{i-1} q w_i...w_n
        Example: 01 q3 10⊔  (head is on '1' at position 2)
        """
        # Trim trailing blanks for display
        t = list(tape)
        while len(t) > 1 and t[-1] == BLANK and head < len(t) - 1:
            t.pop()

        left = ''.join(t[:head])
        right = ''.join(t[head:]) if head < len(t) else BLANK
        return f"{left} {state} {right}"

    def get_formal_definition(self):
        """Return the formal tuple string."""
        q_set = '{' + ', '.join(self.states) + '}'
        sigma = '{' + ', '.join(self.input_alphabet) + '}'
        gamma = '{' + ', '.join(self.tape_alphabet) + '}'
        reject_state = self.reject_state if self.reject_state is not None else '—'
        return (
            f"M = (Q, \u03a3, \u0393, \u03b4, {self.initial_state}, "
            f"{self.accept_state}, {reject_state})\n"
            f"  Q = {q_set}\n"
            f"  \u03a3 = {sigma}\n"
            f"  \u0393 = {gamma}"
        )

    def get_transition_table(self):
        """Return δ as a list of rows for table display.
        Each row: (state, read, new_state, write, direction)
        """
        rows = []
        for (from_s, read_sym), (to_s, write_sym, direction) in sorted(self.transitions.items()):
            rows.append((from_s, read_sym, to_s, write_sym, direction))
        return rows

    def get_transition_labels(self):
        """Group transitions for display: (from, to) -> [labels].
        Label format: 'read -> write, D'
        """
        labels = {}
        for (from_s, read_sym), (to_s, write_sym, direction) in self.transitions.items():
            key = (from_s, to_s)
            label = f"{read_sym}\u2192{write_sym},{direction}"
            if key not in labels:
                labels[key] = []
            labels[key].append(label)
        return {k: '\n'.join(v) for k, v in labels.items()}

    @staticmethod
    def example():
        return f"""# TM: Uw
States: q0, q1, q2, q_accept, q_reject
Input Alphabet: a, b
Tape Alphabet: a, {BLANK}, b
Initial: q0
Accept: q_accept
Reject: q_reject
Transitions:
q0, a -> q1, {BLANK}, R
q0, b -> q2, {BLANK}, R
q1, a -> q1, a, R
q1, b -> q2, a, R
q1, {BLANK} -> q_accept, a, R
q2, a -> q1, b, R
q2, b -> q2, b, R
q2, {BLANK} -> q_accept, b, R"""

    @staticmethod
    def example2():
        return f"""# TM: w#w
States: q0, q1, q2, q3, q4, q5, q6, q7, q_accept
Input Alphabet: a, b, $, X, Y
Tape Alphabet: a, b, {BLANK}, $, #, X, Y
Initial: q0
Accept: q_accept
Transitions:
q0, a -> q0, a, R
q0, b -> q0, b, R
q0, {BLANK} -> q1, $, L
q1, a -> q1, a, L
q1, b -> q1, b, L
q1, {BLANK} -> q2, {BLANK}, R
q2, $ -> q7, #, L
q2, X -> q2, X, R
q2, Y -> q2, Y, R
q2, a -> q3, X, R
q2, b -> q5, Y, R
q3, $ -> q3, $, R
q3, a -> q3, a, R
q3, b -> q3, b, R
q3, {BLANK} -> q4, a, L
q4, $ -> q4, $, L
q4, X -> q4, X, L
q4, Y -> q4, Y, L
q4, a -> q4, a, L
q4, b -> q4, b, L
q4, {BLANK} -> q2, {BLANK}, R
q5, $ -> q5, $, R
q5, a -> q5, a, R
q5, b -> q5, b, R
q5, {BLANK} -> q6, b, L
q6, $ -> q6, $, L
q6, X -> q6, X, L
q6, Y -> q6, Y, L
q6, a -> q6, a, L
q6, b -> q6, b, L
q6, {BLANK} -> q2, {BLANK}, R
q7, X -> q7, a, L
q7, Y -> q7, b, L
q7, {BLANK} -> q_accept, {BLANK}, R"""
