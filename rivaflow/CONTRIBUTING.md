# Contributing to RivaFlow 🥋

Thank you for your interest in contributing to RivaFlow! We welcome contributions from the BJJ community.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Our Standards

**DO:**
- Be respectful and constructive in discussions
- Welcome newcomers and help them get started
- Give and receive feedback gracefully
- Focus on what's best for the community
- Show empathy and kindness

**DON'T:**
- Use hostile or derogatory language
- Make personal attacks
- Publish others' private information
- Engage in trolling or harassment

### Enforcement

Violations of the Code of Conduct can be reported to [security@rivaflow.com]. All complaints will be reviewed and investigated.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Basic knowledge of FastAPI and/or Typer
- BJJ training experience (helpful for context, not required)

### Find an Issue

1. Browse [open issues](https://github.com/RubyWolff27/rivaflow/issues)
2. Look for issues tagged `good-first-issue` or `help-wanted`
3. Comment on the issue to claim it
4. Wait for maintainer approval before starting work

**Not sure what to work on?** Ask in Discussions!

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/rivaflow.git
cd rivaflow

# Add upstream remote
git remote add upstream https://github.com/rivaflow/rivaflow.git
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt  # Development dependencies
```

### 3. Set Up Database

```bash
# Initialize local database
python -c "from rivaflow.db.database import init_db; init_db()"

# Run migrations
python rivaflow/db/migrate.py
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Generate a secret key
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env

# Edit .env with your settings
```

### 5. Verify Installation

```bash
# Run tests
pytest

# Try CLI
rivaflow --help

# Try API
uvicorn rivaflow.api.main:app --reload
# Visit http://localhost:8000/docs
```

---

## How to Contribute

### Types of Contributions

1. **🐛 Bug Fixes**
   - Fix reported bugs
   - Add regression tests
   - Update documentation if needed

2. **✨ New Features**
   - Discuss in issue first
   - Follow existing patterns
   - Add tests and docs
   - Update CHANGELOG.md

3. **📚 Documentation**
   - Fix typos
   - Improve clarity
   - Add examples
   - Translate (future)

4. **🧪 Testing**
   - Add missing tests
   - Improve test coverage
   - Add integration tests

5. **♿ Accessibility**
   - Improve CLI output
   - Add colorblind-friendly themes
   - Screen reader compatibility

### Contribution Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make changes**
   - Write code
   - Add tests
   - Update docs
   - Run tests locally

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Add amazing feature

   Detailed description of what changed and why.

   Fixes #123"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Fill out PR template
   - Link related issues

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines (PEP 8)
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commits follow conventional commits format
- [ ] No merge conflicts with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if applicable)
CLI output or API responses

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. **Automated Checks**
   - Tests must pass
   - Linting must pass
   - Code coverage shouldn't decrease

2. **Code Review**
   - At least 1 approving review required
   - Address all review comments
   - Maintain discussion in PR thread

3. **Merge**
   - Maintainer will merge when approved
   - Use "Squash and merge" for clean history
   - Delete branch after merge

---

## Coding Standards

### Python Style

- Follow **PEP 8**
- Use **type hints** for function signatures
- Write **docstrings** for all public functions
- Maximum line length: **100 characters**
- Use **f-strings** for formatting
- Prefer **explicit** over implicit

### Code Quality Tools

```bash
# Linting
ruff check .

# Type checking
mypy rivaflow/ --ignore-missing-imports

# Formatting
black .

# Import sorting
isort .
```

### Commit Messages

Follow **Conventional Commits:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, not CSS)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(cli): Add session export command

Add new `rivaflow export` command to export all training data
to JSON format. Supports GDPR data portability requirements.

Fixes #42
```

```
fix(auth): Prevent password reset token reuse

Hash password reset tokens before storing in database.
Tokens can no longer be reused after password reset.

Addresses security concern in #123
```

### Code Organization

```
rivaflow/
├── cli/              # CLI commands (Typer)
│   ├── commands/     # Individual command modules
│   └── utils/        # CLI utilities
├── api/              # Web API (FastAPI)
│   ├── routes/       # API endpoints
│   └── middleware/   # API middleware
├── core/             # Business logic
│   ├── services/     # Service layer
│   └── middleware/   # App middleware
├── db/               # Database layer
│   ├── repositories/ # Data access layer
│   └── migrations/   # SQL migrations
└── tests/            # Test suite
    ├── unit/         # Unit tests
    └── integration/  # Integration tests
```

---

## Testing Guidelines

### Writing Tests

```python
# tests/unit/test_session_service.py
import pytest
from rivaflow.core.services.session_service import SessionService

def test_create_session():
    """Test session creation with valid data."""
    service = SessionService()
    session = service.create_session(
        user_id=1,
        session_date=date.today(),
        class_type="gi",
        gym_name="Test Gym",
    )
    assert session["id"] is not None
    assert session["class_type"] == "gi"
```

### Test Coverage Goals

- **Overall:** >80%
- **Core services:** >90%
- **Critical paths:** 100% (auth, session logging, data export)

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=rivaflow --cov-report=html

# Specific file
pytest tests/unit/test_session_service.py

# Specific test
pytest tests/unit/test_session_service.py::test_create_session

# Watch mode (requires pytest-watch)
ptw
```

### Test Database

Use separate test database:
```python
# conftest.py
@pytest.fixture
def test_db():
    """Create isolated test database."""
    # Setup test DB
    yield db
    # Teardown
```

---

## Documentation

### Code Documentation

**Docstrings required for:**
- All public functions
- All classes
- Complex algorithms

**Format:**
```python
def create_session(
    user_id: int,
    session_date: date,
    class_type: str,
) -> dict:
    """
    Create a new training session.

    Args:
        user_id: ID of the user logging the session
        session_date: Date of the session
        class_type: Type of class (gi, no-gi, etc.)

    Returns:
        Dictionary containing the created session data

    Raises:
        ValueError: If session_date is in the future
        ValidationError: If class_type is invalid
    """
    ...
```

### User Documentation

- Update README.md for new features
- Add examples to docs/
- Update API documentation (OpenAPI)
- Add FAQ entries for common questions

---

## Community

### Get Help

- **GitHub Discussions:** For questions and ideas
- **GitHub Issues:** For bugs and feature requests
- **Discord:** [Coming soon] For real-time chat
- **Email:** support@rivaflow.com

### Stay Updated

- Watch the repository for notifications
- Follow releases
- Read CHANGELOG.md
- Check project roadmap

### Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub Contributors page
- Annual contributor highlights

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

Don't hesitate to ask! We're here to help:

- Open a [Discussion](https://github.com/rivaflow/rivaflow/discussions)
- Comment on an existing issue
- Email support@rivaflow.com

**Thank you for contributing to RivaFlow! 🥋**

_Train with intent. Code with purpose._
