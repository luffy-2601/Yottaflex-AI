# Contributing to FreightGuard AI

Thank you for your interest in contributing to **FreightGuard AI**! We welcome community contributions, bug reports, feature enhancements, and documentation improvements.

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Git
- Virtual environment (`venv` recommended)

### 2. Clone and Setup Environment
```bash
git clone https://github.com/luffy-2601/Yottaflex-AI.git
cd Yottaflex-AI

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate Test Data & Verify Pipeline
```bash
# Generate starter dataset (150 invoices in ~1s)
python scripts/run_all.py --scale starter

# Run full test suite (all 32 tests must pass)
python -m pytest
```

---

## 🔄 Branching & Pull Request Workflow

1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Make your changes following PEP 8 conventions.
3. Run automated tests to ensure no regressions:
   ```bash
   pytest
   ```
4. Commit your changes with clear, structured messages:
   ```bash
   git commit -m "feat(audit): add support for intermodal rail accessorial validation"
   ```
5. Push to your branch and open a Pull Request against `main`.

---

## 🧪 Testing Guidelines

- All business logic additions must include unit tests in `tests/`.
- Ensure high test coverage and zero regressions.
- If adding new API endpoints, add tests in `tests/test_api.py`.
- If modifying authentication or security, add tests in `tests/test_auth.py`.

---

## 📜 Code of Conduct

Please treat all contributors with respect and professionalism. We are committed to providing a friendly, safe, and welcoming environment for all.
