"""Turing Machine (TM) model.

Definition (7-tuple): (Q, Sigma, Gamma, delta, q0, q_accept, q_reject)
- Q: finite set of states
- Sigma: input alphabet (no blank symbol)
- Gamma: tape alphabet, where blank in Gamma and Sigma subset Gamma
- delta: Q x Gamma -> Q x Gamma x {L, R}
- q0: start state
- q_accept: accept state (halts immediately)
- q_reject: reject state (halts immediately, q_accept != q_reject)

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
        if tm.reject_state is None:
            errors.append("No se definio estado de rechazo")
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
        """Return the formal 7-tuple string."""
        q_set = '{' + ', '.join(self.states) + '}'
        sigma = '{' + ', '.join(self.input_alphabet) + '}'
        gamma = '{' + ', '.join(self.tape_alphabet) + '}'
        return (
            f"M = (Q, \u03a3, \u0393, \u03b4, {self.initial_state}, "
            f"{self.accept_state}, {self.reject_state})\n"
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
        return f"""# TM: Acepta {{0^(2^n) | n >= 0}}
# Potencias de 2 en ceros
States: q1, q2, q3, q4, q5, q_accept, q_reject
Input Alphabet: 0
Tape Alphabet: 0, x, {BLANK}
Initial: q1
Accept: q_accept
Reject: q_reject
Transitions:
q1, {BLANK} -> q_reject, {BLANK}, R
q1, x -> q_reject, x, R
q1, 0 -> q2, {BLANK}, R
q2, x -> q2, x, R
q2, {BLANK} -> q_accept, {BLANK}, R
q2, 0 -> q3, x, R
q3, x -> q3, x, R
q3, 0 -> q4, 0, R
q3, {BLANK} -> q5, {BLANK}, L
q4, x -> q4, x, R
q4, 0 -> q3, x, R
q4, {BLANK} -> q_reject, {BLANK}, R
q5, 0 -> q5, 0, L
q5, x -> q5, x, L
q5, {BLANK} -> q2, {BLANK}, R"""

    @staticmethod
    def example2():
        return f"""# TM: Acepta {{w#w | w in {{0,1}}*}}
States: q1, q2, q3, q4, q5, q6, q7, q8, q_accept, q_reject
Input Alphabet: 0, 1, #
Tape Alphabet: 0, 1, #, x, {BLANK}
Initial: q1
Accept: q_accept
Reject: q_reject
Transitions:
q1, 0 -> q2, x, R
q1, 1 -> q3, x, R
q1, # -> q7, #, R
q2, 0 -> q2, 0, R
q2, 1 -> q2, 1, R
q2, # -> q4, #, R
q4, x -> q4, x, R
q4, 0 -> q6, x, L
q4, {BLANK} -> q_reject, {BLANK}, R
q4, 1 -> q_reject, 1, R
q3, 0 -> q3, 0, R
q3, 1 -> q3, 1, R
q3, # -> q5, #, R
q5, x -> q5, x, R
q5, 1 -> q6, x, L
q5, {BLANK} -> q_reject, {BLANK}, R
q5, 0 -> q_reject, 0, R
q6, x -> q6, x, L
q6, # -> q8, #, L
q6, 0 -> q6, 0, L
q6, 1 -> q6, 1, L
q8, 0 -> q8, 0, L
q8, 1 -> q8, 1, L
q8, x -> q1, x, R
q7, x -> q7, x, R
q7, {BLANK} -> q_accept, {BLANK}, R
q7, 0 -> q_reject, 0, R
q7, 1 -> q_reject, 1, R"""
