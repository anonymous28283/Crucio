# Crucio

**Crucio** is a grammar inference tool that learns context-free grammars from a set of example inputs. It consists of two main phases: inference and evaluation.

## Installation

1. **Install dependencies**

   Make sure you have Python 3.6 or later installed. Then install all required libraries:

   ```bash
   pip install -r requirements.txt
   ```

2. **Compile Cython files**

   Crucio uses Cython for performance-critical components. Before running the tool, compile the Cython extensions:

   ```bash
   python setup.py build_ext --inplace
   ```

---

## Usage

### Inference

To infer a grammar from training data, run:

```bash
python3 infer.py ORACLE_CMD TRAIN_DIR LOG_FILE
```

- `ORACLE_CMD`: A shell command that accepts an input string and returns whether it is valid (used for validating candidates during inference).
- `TRAIN_DIR`: Path to the directory containing training examples (e.g., `.txt` files).
- `LOG_FILE`: Path to store the inference results and the inferred grammar.

**Example:**

```bash
python3 infer.py xx/parse_tinyc ./data/train ./output/infer.log
```

---

### Evaluation

To evaluate the inferred grammar using a test dataset:

```bash
python3 eval.py TEST_DIR LOG_FILE
```

- `TEST_DIR`: Path to the directory containing test examples.
- `LOG_FILE`: The same log file produced by `infer.py`, which contains the grammar used for evaluation.

**Example:**

```bash
python3 eval.py ./data/test ./output/infer.log
```

---



## Requirements

- Python 3.6+
- Cython
- Other packages listed in `requirements.txt`

To install Cython separately if needed:

```bash
pip install cython
```

---

## Notes

- Make sure to compile Cython files **before** running inference or evaluation.
- The oracle should be executable from the shell and return appropriate status codes or output for correctness checking.
- Training and test files are expected to be text-based input samples, one sample per file or per line depending on implementation.

---
