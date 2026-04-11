# AutomataLab

An interactive desktop application for creating, visualizing, and testing formal language constructs. Built as a study tool for formal language theory courses.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

### Supported Formal Language Types

| Type | Interactive Canvas | Step-by-Step Simulation | Import/Export |
|------|:-:|:-:|:-:|
| **DFA** (Deterministic Finite Automaton) | Yes | Yes | Yes |
| **NFA** (Non-deterministic Finite Automaton) | Yes | Yes | Yes |
| **PDA** (Pushdown Automaton) | Yes | Yes | Yes |
| **Regular Expressions** (Formal) | NFA via Thompson's | Trace | - |
| **CFG** (Context-Free Grammar) | Parse Tree | Derivation | - |
| **TM** (Turing Machine) | Yes | Yes | Yes |

### Interactive Visual Editor
- Drag-and-drop state placement
- Toolbar modes: add states, transitions, set initial/accept states, delete
- Real-time diagram rendering with labeled transitions
- Hover and selection highlighting

### Testing & Simulation
- Instant string acceptance/rejection testing
- Step-by-step simulation with state highlighting
- NFA: epsilon closure computation and multi-path traces
- PDA: full stack trace visualization
- CFG: leftmost derivation display and parse tree rendering

### Regular Expressions (Formal)
- Formal RE operators: `a`, `ε`, `∅`, `R₁∪R₂`, `R₁R₂`, `R*`, `R⁺`, `Σ`
- Thompson's construction (RE to NFA conversion)
- NFA visualization of compiled expression
- Symbol insertion buttons for special characters
- 8 built-in syllabus examples with batch testing

### Context-Free Grammars
- Production rule editor with auto-detection of variables and terminals
- Parse tree visualization on scrollable canvas
- String generation from grammar rules
- Ambiguity checking (multiple leftmost derivations)
- Formal definition display: `G = (V, Σ, R, S)`

### Turing Machines
- Interactive single-tape Turing machine editor
- Transition format `read -> write, direction`
- Tape visualization with head position highlighting
- Step-by-step execution with configuration trace
- Dedicated accept and reject states
- Import/export in text format
- Built-in examples including `Uw` and `w#w`

## Installation

### Prerequisites
- Python 3.8+

### Setup
```bash
git clone https://github.com/yourusername/LF-Creator.git
cd LF-Creator
pip install -r requirements.txt
```

### Run
```bash
python main.py
```

### Build Executable (.exe)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "AutomataLab" main.py
```
The executable will be in `dist/AutomataLab.exe`.

### Debian / Ubuntu

AutomataLab is primarily designed for Windows 11. However, basic support has been added for Ubuntu 24.04. Behavior may not be fully optimized, but the main features should work correctly.

The application UI is in Spanish, since it is intended for students at my university in Spain.

#### Run with an automatic virtualenv
```bash
chmod +x scripts/run_debian.sh
./scripts/run_debian.sh
```

This script:
- uses `python3.12` if available
- otherwise uses `python3` only if the default version is already `3.12` or newer
- requires Python 3.12 or newer
- creates `.venv` if it does not exist
- installs or updates the Python dependencies inside that environment
- launches `main.py` directly with that virtual environment

#### Common Debian / Ubuntu issues

If the script fails because Python, virtual environments or Tkinter are missing:

```bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev python3-tk -y
```

If the script fails because your Python version is older than `3.12`, install a newer Python and make sure either `python3.12 --version` or the default `python3 --version` reports `3.12` or newer before running the script again.

This script is intended for Debian / Ubuntu style environments.
It is only intended for systems where the default `python3` is already `3.12` or newer.

## Usage

### DFA / NFA / PDA (Interactive Canvas)

1. Use the **toolbar** to select a mode (Add State, Transition, Initial, Accept, Delete)
2. **Click on the canvas** to add states
3. **Click two states** in Transition mode to add a transition (a dialog will ask for the symbol)
4. **Drag states** in Select mode to reposition them
5. Enter a string in the test field and press **Probar** (Test) or **Paso a paso** (Step-by-step)
6. Use **Import/Export** to load or save text-based definitions

#### Text Definition Format (DFA example)
```
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
q2, 1 -> q2
```

### Regular Expressions

1. Type a formal regular expression (e.g., `(a∪b)*abb`)
2. Set the alphabet (e.g., `a, b`)
3. Press **Construir** to build the NFA via Thompson's construction
4. Test individual strings or use batch testing

### Context-Free Grammars

1. Write production rules (e.g., `S -> aSb | ε`)
2. Press **Construir** to parse the grammar
3. Test strings to see leftmost derivations and parse trees
4. Use **Generar** to enumerate strings in the language
5. Use **Verificar Ambiguedad** to check if a string has multiple derivations

### Turing Machines

1. Use the canvas to create states and transitions
2. Mark one halt state as **Accept** and another as **Reject**
3. Add transitions in the form `read -> write, direction`
4. Enter an input string and press **Ejecutar** to run the machine
5. Use **Paso a paso** to inspect the tape, head movement, and configurations
6. Load one of the built-in examples such as `Uw` or `w#w`

## Project Structure

```
LF-Creator/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── core/
│   ├── dfa.py               # DFA model & parser
│   ├── nfa.py               # NFA model with epsilon closure
│   ├── pda.py               # PDA model with stack simulation
│   ├── cfg.py               # CFG model with derivation & parse trees
│   └── regex_formal.py      # Formal RE parser & Thompson's construction
└── gui/
    ├── app.py               # Main window with tabbed interface
    ├── base_tab.py          # Base class for editor tabs
    ├── canvas_renderer.py   # Interactive automata canvas widget
    ├── dfa_tab.py           # DFA interactive editor
    ├── nfa_tab.py           # NFA interactive editor
    ├── pda_tab.py           # PDA interactive editor
    ├── regex_tab.py         # Formal RE editor
    └── cfg_tab.py           # CFG editor with parse tree view
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` / `F5` | Build current automaton |
| `Ctrl+T` | Test current string |
| `Enter` | Submit test string |

## Dependencies

- **Pillow** - Image handling
- **graphviz** - Graph visualization (optional)

## License

MIT

---

Created by **Alfonso** and **Claude**.
