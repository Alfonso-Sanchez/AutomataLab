"""Formal regular expression parser and NFA converter (Thompson's construction).

This module handles formal regular expressions as defined in university-level
formal language theory courses. It does NOT use Python regex.

Supported operators (by precedence, highest first):
    *   Kleene star
    +   Kleene plus (shorthand for RR*)
    .   Concatenation (implicit)
    U   Union

Grammar:
    expr   -> term ('U' term)*
    term   -> factor factor*
    factor -> base ('*' | '+')*
    base   -> LITERAL | EPSILON | EMPTY | SIGMA | '(' expr ')'
"""

from core.nfa import NFA


# ---------------------------------------------------------------------------
# AST node constructors (tuples for simplicity)
# ---------------------------------------------------------------------------

def _lit(ch):
    return ('literal', ch)

def _eps():
    return ('epsilon',)

def _empty():
    return ('empty',)

def _union(left, right):
    return ('union', left, right)

def _concat(left, right):
    return ('concat', left, right)

def _star(child):
    return ('star', child)

def _plus(child):
    return ('plus', child)


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

_UNION_CHARS = {'\u222a', '+', '|', 'U'}  # ∪, +, |, U
_EPSILON_STRS = {'\u03b5', 'eps', 'epsilon', '\u03b5'}  # ε
_EMPTY_CHAR = '\u2205'  # ∅
_SIGMA_CHAR = '\u03a3'  # Σ
_STAR_CHAR = '*'
_PLUS_CHARS = {'\u207a', '\u207A'}  # ⁺ (superscript plus)
_OPEN = '('
_CLOSE = ')'


def _tokenise(text):
    """Convert input string into a list of tokens.

    Token types:
        ('LIT', ch)      - literal character
        ('EPS',)         - epsilon
        ('EMPTY',)       - empty set
        ('SIGMA',)       - sigma (alphabet wildcard)
        ('UNION',)       - union operator
        ('STAR',)        - Kleene star
        ('PLUS',)        - Kleene plus
        ('LPAREN',)      - (
        ('RPAREN',)      - )
    """
    tokens = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Skip whitespace and explicit concatenation dot
        if ch in (' ', '\t', '\u25e6', '\u2218', '\u00b7'):
            # ◦ ∘ · are concatenation markers - just skip
            i += 1
            continue

        # Epsilon words
        if ch == '\u03b5':  # ε
            tokens.append(('EPS',))
            i += 1
            continue
        if text[i:i+7].lower() == 'epsilon':
            tokens.append(('EPS',))
            i += 7
            continue
        if text[i:i+3].lower() == 'eps' and (i + 3 >= n or not text[i+3].isalnum()):
            tokens.append(('EPS',))
            i += 3
            continue

        # Empty set
        if ch == _EMPTY_CHAR:
            tokens.append(('EMPTY',))
            i += 1
            continue

        # Sigma
        if ch == _SIGMA_CHAR:
            tokens.append(('SIGMA',))
            i += 1
            continue

        # Parentheses
        if ch == _OPEN:
            tokens.append(('LPAREN',))
            i += 1
            continue
        if ch == _CLOSE:
            tokens.append(('RPAREN',))
            i += 1
            continue

        # Star
        if ch == _STAR_CHAR:
            tokens.append(('STAR',))
            i += 1
            continue

        # Superscript plus ⁺
        if ch in _PLUS_CHARS:
            tokens.append(('PLUS',))
            i += 1
            continue

        # Union or plus (context-dependent for '+')
        if ch == '\u222a':  # ∪ always union
            tokens.append(('UNION',))
            i += 1
            continue
        if ch == '|':  # | always union
            tokens.append(('UNION',))
            i += 1
            continue

        # '+' is ambiguous: it's union between operands, plus after * or ) or literal
        if ch == '+':
            # Determine context: if previous token is a "value" token, it's plus
            if tokens and tokens[-1][0] in ('RPAREN', 'STAR', 'PLUS', 'LIT', 'EPS', 'EMPTY', 'SIGMA'):
                tokens.append(('PLUS',))
            else:
                tokens.append(('UNION',))
            i += 1
            continue

        # Literal: lowercase letters, digits, uppercase that aren't reserved
        if ch.isalnum() and ch not in ('U',):
            tokens.append(('LIT', ch))
            i += 1
            continue

        # 'U' as union only if it looks like an operator (between operands)
        if ch == 'U':
            # Check if surrounded by operands - treat as union
            if tokens and tokens[-1][0] in ('RPAREN', 'STAR', 'PLUS', 'LIT', 'EPS', 'EMPTY', 'SIGMA'):
                # Peek ahead to see if next char starts an operand
                j = i + 1
                while j < n and text[j] in (' ', '\t'):
                    j += 1
                if j < n and (text[j] in (_OPEN, _EMPTY_CHAR, _SIGMA_CHAR, '\u03b5') or
                              text[j].isalnum() or text[j:j+3].lower() == 'eps'):
                    tokens.append(('UNION',))
                    i += 1
                    continue
            # Otherwise treat as literal
            tokens.append(('LIT', ch))
            i += 1
            continue

        # Skip unknown characters
        i += 1

    return tokens


# ---------------------------------------------------------------------------
# Recursive descent parser
# ---------------------------------------------------------------------------

class _Parser:
    """Recursive descent parser for formal regular expressions.

    Grammar (precedence low to high):
        expr   -> term (UNION term)*
        term   -> factor+
        factor -> base (STAR | PLUS)*
        base   -> LIT | EPS | EMPTY | SIGMA | LPAREN expr RPAREN
    """

    def __init__(self, tokens, alphabet):
        self.tokens = tokens
        self.pos = 0
        self.alphabet = alphabet or []
        self.errors = []

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, ttype):
        tok = self.peek()
        if tok is None or tok[0] != ttype:
            self.errors.append(f"Se esperaba '{ttype}', se encontro '{tok}'")
            return None
        return self.consume()

    def parse(self):
        if not self.tokens:
            self.errors.append("Expresion vacia")
            return None
        tree = self.parse_expr()
        if self.pos < len(self.tokens):
            self.errors.append(
                f"Tokens inesperados despues de la expresion: "
                f"{self.tokens[self.pos:]}"
            )
        return tree

    def parse_expr(self):
        """expr -> term (UNION term)*"""
        left = self.parse_term()
        if left is None:
            return None
        while self.peek() and self.peek()[0] == 'UNION':
            self.consume()  # eat UNION
            right = self.parse_term()
            if right is None:
                self.errors.append("Se esperaba expresion despues de union")
                return left
            left = _union(left, right)
        return left

    def parse_term(self):
        """term -> factor+  (implicit concatenation)"""
        left = self.parse_factor()
        if left is None:
            return None
        # Concatenation is implicit: keep parsing factors while the next token
        # can start a base expression
        while self.peek() and self.peek()[0] in ('LIT', 'EPS', 'EMPTY', 'SIGMA', 'LPAREN'):
            right = self.parse_factor()
            if right is None:
                break
            left = _concat(left, right)
        return left

    def parse_factor(self):
        """factor -> base (STAR | PLUS)*"""
        node = self.parse_base()
        if node is None:
            return None
        while self.peek() and self.peek()[0] in ('STAR', 'PLUS'):
            tok = self.consume()
            if tok[0] == 'STAR':
                node = _star(node)
            else:
                node = _plus(node)
        return node

    def parse_base(self):
        """base -> LIT | EPS | EMPTY | SIGMA | LPAREN expr RPAREN"""
        tok = self.peek()
        if tok is None:
            self.errors.append("Se esperaba expresion, se encontro fin de entrada")
            return None

        if tok[0] == 'LIT':
            self.consume()
            return _lit(tok[1])

        if tok[0] == 'EPS':
            self.consume()
            return _eps()

        if tok[0] == 'EMPTY':
            self.consume()
            return _empty()

        if tok[0] == 'SIGMA':
            self.consume()
            # Expand Sigma to union of all alphabet symbols
            if not self.alphabet:
                self.errors.append(
                    "Se uso Sigma pero no se definio un alfabeto"
                )
                return _empty()
            if len(self.alphabet) == 1:
                return _lit(self.alphabet[0])
            node = _lit(self.alphabet[0])
            for ch in self.alphabet[1:]:
                node = _union(node, _lit(ch))
            return node

        if tok[0] == 'LPAREN':
            self.consume()
            node = self.parse_expr()
            if not self.expect('RPAREN'):
                self.errors.append("Falta parentesis de cierre ')'")
            return node

        self.errors.append(f"Token inesperado: {tok}")
        self.consume()  # skip it
        return None


# ---------------------------------------------------------------------------
# Thompson's construction
# ---------------------------------------------------------------------------

_state_counter = 0


def _new_state():
    global _state_counter
    name = f"q{_state_counter}"
    _state_counter += 1
    return name


def _reset_states():
    global _state_counter
    _state_counter = 0


def _thompson(tree, alphabet):
    """Build an NFA fragment from an AST node using Thompson's construction.

    Returns (nfa, start_state, accept_state).
    Each fragment has exactly one start state and one accept state.
    """
    if tree is None:
        # Shouldn't happen, but handle gracefully
        return _thompson_empty(alphabet)

    kind = tree[0]

    if kind == 'literal':
        return _thompson_literal(tree[1], alphabet)
    elif kind == 'epsilon':
        return _thompson_epsilon(alphabet)
    elif kind == 'empty':
        return _thompson_empty(alphabet)
    elif kind == 'union':
        return _thompson_union(tree[1], tree[2], alphabet)
    elif kind == 'concat':
        return _thompson_concat(tree[1], tree[2], alphabet)
    elif kind == 'star':
        return _thompson_star(tree[1], alphabet)
    elif kind == 'plus':
        # R+ = R R*
        return _thompson_plus(tree[1], alphabet)
    else:
        raise ValueError(f"Nodo AST desconocido: {kind}")


def _thompson_literal(ch, alphabet):
    """Literal: two states connected by transition on ch."""
    s = _new_state()
    a = _new_state()
    nfa = NFA()
    nfa.states = [s, a]
    nfa.alphabet = list(alphabet)
    if ch not in nfa.alphabet:
        nfa.alphabet.append(ch)
    nfa.initial_state = s
    nfa.accept_states = {a}
    nfa.transitions = {(s, ch): {a}}
    return nfa, s, a


def _thompson_epsilon(alphabet):
    """Epsilon: single state that is both start and accept."""
    s = _new_state()
    a = _new_state()
    nfa = NFA()
    nfa.states = [s, a]
    nfa.alphabet = list(alphabet)
    nfa.initial_state = s
    nfa.accept_states = {a}
    nfa.transitions = {(s, '\u03b5'): {a}}  # ε-transition
    return nfa, s, a


def _thompson_empty(alphabet):
    """Empty set: one start state, one non-accepting dead state."""
    s = _new_state()
    a = _new_state()  # NOT an accept state
    nfa = NFA()
    nfa.states = [s, a]
    nfa.alphabet = list(alphabet)
    nfa.initial_state = s
    nfa.accept_states = set()  # No accept states
    nfa.transitions = {}
    return nfa, s, a


def _merge_nfa(target, source):
    """Merge source NFA states and transitions into target."""
    for st in source.states:
        if st not in target.states:
            target.states.append(st)
    for sym in source.alphabet:
        if sym not in target.alphabet:
            target.alphabet.append(sym)
    for key, val in source.transitions.items():
        if key in target.transitions:
            target.transitions[key] = target.transitions[key] | val
        else:
            target.transitions[key] = set(val)


def _add_epsilon(nfa, from_s, to_s):
    """Add an epsilon transition."""
    key = (from_s, '\u03b5')
    if key not in nfa.transitions:
        nfa.transitions[key] = set()
    nfa.transitions[key].add(to_s)


def _thompson_union(left_tree, right_tree, alphabet):
    """Union: new start with epsilon to both sub-NFAs, both accepts epsilon to new accept."""
    nfa1, s1, a1 = _thompson(left_tree, alphabet)
    nfa2, s2, a2 = _thompson(right_tree, alphabet)

    s = _new_state()
    a = _new_state()

    result = NFA()
    result.states = [s]
    result.alphabet = list(alphabet)
    result.transitions = {}

    _merge_nfa(result, nfa1)
    _merge_nfa(result, nfa2)

    result.states.append(a)
    result.initial_state = s
    result.accept_states = {a}

    # Remove old accept states
    # (they are no longer accept states in the combined NFA)

    _add_epsilon(result, s, s1)
    _add_epsilon(result, s, s2)
    _add_epsilon(result, a1, a)
    _add_epsilon(result, a2, a)

    return result, s, a


def _thompson_concat(left_tree, right_tree, alphabet):
    """Concatenation: chain two NFAs, epsilon from first accept to second start."""
    nfa1, s1, a1 = _thompson(left_tree, alphabet)
    nfa2, s2, a2 = _thompson(right_tree, alphabet)

    result = NFA()
    result.states = []
    result.alphabet = list(alphabet)
    result.transitions = {}

    _merge_nfa(result, nfa1)
    _merge_nfa(result, nfa2)

    result.initial_state = s1
    result.accept_states = {a2}

    _add_epsilon(result, a1, s2)

    return result, s1, a2


def _thompson_star(child_tree, alphabet):
    """Kleene star: new start (accept) with epsilon to child, child accept back to start."""
    nfa1, s1, a1 = _thompson(child_tree, alphabet)

    s = _new_state()
    a = _new_state()

    result = NFA()
    result.states = [s]
    result.alphabet = list(alphabet)
    result.transitions = {}

    _merge_nfa(result, nfa1)

    result.states.append(a)
    result.initial_state = s
    result.accept_states = {a}

    _add_epsilon(result, s, s1)   # new start to child start
    _add_epsilon(result, s, a)    # new start to new accept (skip - matches epsilon)
    _add_epsilon(result, a1, s1)  # child accept back to child start (loop)
    _add_epsilon(result, a1, a)   # child accept to new accept

    return result, s, a


def _thompson_plus(child_tree, alphabet):
    """Kleene plus: like star but without the skip-epsilon (must go through child at least once)."""
    nfa1, s1, a1 = _thompson(child_tree, alphabet)

    s = _new_state()
    a = _new_state()

    result = NFA()
    result.states = [s]
    result.alphabet = list(alphabet)
    result.transitions = {}

    _merge_nfa(result, nfa1)

    result.states.append(a)
    result.initial_state = s
    result.accept_states = {a}

    _add_epsilon(result, s, s1)   # new start to child start
    # NO epsilon from s to a (must match at least once)
    _add_epsilon(result, a1, s1)  # child accept back to child start (loop)
    _add_epsilon(result, a1, a)   # child accept to new accept

    return result, s, a


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class FormalRegex:
    """Formal regular expression parser and evaluator.

    This handles the formal RE notation from formal language theory courses:
      - Literals (a, b, 0, 1, ...)
      - Epsilon (empty string)
      - Empty set
      - Union (R1 U R2)
      - Concatenation (R1R2, implicit)
      - Kleene star (R*)
      - Kleene plus (R+, shorthand for RR*)
      - Sigma (alphabet wildcard)

    Precedence: * > concatenation > union
    """

    @staticmethod
    def parse(text, alphabet=None):
        """Parse a formal RE string into a syntax tree.

        Args:
            text: The regular expression string.
            alphabet: Optional list of alphabet symbols. Required if Sigma is used.

        Returns:
            (tree, errors) where tree is a nested tuple AST and errors is a list
            of error strings. If errors is non-empty, tree may be None.

        Tree node types:
            ('literal', char)
            ('epsilon',)
            ('empty',)
            ('union', left, right)
            ('concat', left, right)
            ('star', child)
            ('plus', child)
        """
        text = text.strip()
        if not text:
            return None, ["Expresion vacia"]

        tokens = _tokenise(text)
        if not tokens:
            return None, ["No se pudo tokenizar la expresion"]

        parser = _Parser(tokens, alphabet or [])
        tree = parser.parse()
        return tree, parser.errors

    @staticmethod
    def to_nfa(tree, alphabet=None):
        """Thompson's construction: convert RE tree to NFA.

        Args:
            tree: AST from parse().
            alphabet: Optional list of alphabet symbols.

        Returns:
            An NFA object (from core.nfa).
        """
        _reset_states()
        alph = list(alphabet) if alphabet else []

        # Collect all literals from the tree to ensure alphabet is complete
        def collect_literals(node):
            if node is None:
                return
            if node[0] == 'literal':
                if node[1] not in alph:
                    alph.append(node[1])
            elif node[0] in ('union', 'concat'):
                collect_literals(node[1])
                collect_literals(node[2])
            elif node[0] in ('star', 'plus'):
                collect_literals(node[1])

        collect_literals(tree)

        nfa, start, accept = _thompson(tree, alph)

        # Clean up alphabet: remove epsilon if accidentally added, sort
        nfa.alphabet = sorted(set(a for a in nfa.alphabet if a != '\u03b5'))

        return nfa

    @staticmethod
    def tree_to_string(tree):
        """Convert an AST back to a human-readable string representation.

        Uses minimal parentheses based on operator precedence.
        """
        if tree is None:
            return ""

        kind = tree[0]

        if kind == 'literal':
            return tree[1]
        elif kind == 'epsilon':
            return '\u03b5'
        elif kind == 'empty':
            return '\u2205'
        elif kind == 'union':
            left_s = FormalRegex.tree_to_string(tree[1])
            right_s = FormalRegex.tree_to_string(tree[2])
            return f"({left_s}\u222a{right_s})"
        elif kind == 'concat':
            left_s = FormalRegex._concat_str(tree[1])
            right_s = FormalRegex._concat_str(tree[2])
            return f"{left_s}{right_s}"
        elif kind == 'star':
            child_s = FormalRegex._postfix_str(tree[1])
            return f"{child_s}*"
        elif kind == 'plus':
            child_s = FormalRegex._postfix_str(tree[1])
            return f"{child_s}\u207a"
        else:
            return "?"

    @staticmethod
    def _concat_str(tree):
        """Helper: wrap union nodes in parens when inside concatenation."""
        if tree[0] == 'union':
            return f"({FormalRegex.tree_to_string(tree)})"
        return FormalRegex.tree_to_string(tree)

    @staticmethod
    def _postfix_str(tree):
        """Helper: wrap union/concat in parens when applying * or +."""
        if tree[0] in ('union', 'concat'):
            inner = FormalRegex.tree_to_string(tree)
            # Remove outer parens if tree_to_string already added them for union
            if tree[0] == 'union':
                return inner  # already has parens from tree_to_string
            return f"({inner})"
        return FormalRegex.tree_to_string(tree)

    @staticmethod
    def test_string(tree, input_string, alphabet=None):
        """Test if a string matches the formal RE by converting to NFA.

        Args:
            tree: AST from parse().
            input_string: String to test.
            alphabet: Optional alphabet.

        Returns:
            (accepted, nfa, trace, message) where:
                accepted: bool
                nfa: the NFA used for testing
                trace: list of (frozenset_of_states, symbol)
                message: result description string
        """
        nfa = FormalRegex.to_nfa(tree, alphabet)
        accepted, trace, msg = nfa.test(input_string)
        return accepted, nfa, trace, msg

    @staticmethod
    def describe(tree):
        """Return a description of what the RE matches."""
        if tree is None:
            return "Expresion invalida"
        kind = tree[0]
        if kind == 'empty':
            return "Lenguaje vacio (no acepta ninguna cadena)"
        if kind == 'epsilon':
            return "Solo acepta la cadena vacia"
        s = FormalRegex.tree_to_string(tree)
        return f"L({s})"

    @staticmethod
    def auto_detect_alphabet(tree):
        """Detect alphabet symbols used in the expression."""
        symbols = set()

        def walk(node):
            if node is None:
                return
            if node[0] == 'literal':
                symbols.add(node[1])
            elif node[0] in ('union', 'concat'):
                walk(node[1])
                walk(node[2])
            elif node[0] in ('star', 'plus'):
                walk(node[1])

        walk(tree)
        return sorted(symbols)

    @staticmethod
    def example():
        """Example 1: strings over {0,1} containing exactly one 1."""
        return "0*10*"

    @staticmethod
    def example2():
        """Example 2: strings over {a,b} ending in 'abb'."""
        return "(a\u222ab)*abb"
