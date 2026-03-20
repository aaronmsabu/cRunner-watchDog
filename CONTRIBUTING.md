# Contributing to Runner Watchdog

First off — **thank you** for considering contributing! Runner Watchdog is an open-source project and we welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code.

---

## 🚀 Quick Start for Contributors

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/runner-watchdog.git
cd runner-watchdog

# 2. Create a feature branch
git checkout -b feat/your-feature-name

# 3. Set up local environment
cp .env.example .env
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Start the stack
docker compose up --build
```

---

## 📋 How to Contribute

### Reporting Bugs

Open an issue with:
- **What happened** (include logs and error messages)
- **What you expected** to happen
- **Steps to reproduce** the issue
- **Environment** (OS, Docker version, Python version)

### Suggesting Features

Open an issue with the `enhancement` label describing:
- The **problem** you're trying to solve
- Your **proposed solution**
- Any **alternatives** you've considered

### Submitting Code

1. Fork the repository
2. Create a feature branch (`feat/...`) or bugfix branch (`fix/...`)
3. Write clear, well-documented code
4. Ensure all Python files pass `python -m py_compile`
5. Submit a pull request with a clear description of the changes

---

## 🧑‍💻 Code Style

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/)
- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`, `chore:`)
- **Docstrings**: Use Google-style or NumPy-style docstrings
- **Type hints**: Preferred for all function signatures

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
