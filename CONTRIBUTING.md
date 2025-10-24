# Contributing to Confy CLI

Thank you for considering contributing to **Confy CLI**! This project was developed with dedication by Brazilian students 🇧🇷 and we value all contributions, whether they are bug fixes, new features, documentation improvements, or tests.

To ensure an organized workflow and a good experience for everyone, please follow the guidelines below.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Environment Setup](#development-environment-setup)
4. [Project Structure](#project-structure)
5. [Contribution Workflow](#contribution-workflow)
6. [Code Standards](#code-standards)
7. [Quality Tools](#quality-tools)
8. [Testing the CLI](#testing-the-cli)
9. [Running the Project Locally](#running-the-project-locally)
10. [Creating a Pull Request](#creating-a-pull-request)
11. [Review Process](#review-process)
12. [Reporting Security Issues](#reporting-security-issues)

## Code of Conduct

We are committed to maintaining a welcoming, safe, and collaborative environment. Everyone should be treated with respect, regardless of age, gender identity, sexual orientation, ethnicity, religion, or experience level.

**Unacceptable behaviors include:**

- Harassment, discrimination, or insults
- Sexualized language or content
- Threats or personal attacks
- Unauthorized disclosure of private information

To report violations, contact: [confy@henriquesebastiao.com](mailto:confy@henriquesebastiao.com)

## Getting Started

### Prerequisites

Before you begin, make sure you have:

- **Git** installed and configured
- **Python 3.13 or higher** (we support Python 3.13+)
- **Poetry** for dependency management (recommended)
- A **GitHub** account

### Verify Your Installation

```bash
python --version
poetry --version
git --version
```

## Development Environment Setup

### 1. Fork the Repository

1. Go to [github.com/confy-security/cli](https://github.com/confy-security/cli)
2. Click the **"Fork"** button in the top right corner
3. This will create a copy of the repository in your account

### 2. Clone Your Fork Locally

```bash
git clone https://github.com/YOUR-USERNAME/cli.git
cd cli
```

### 3. Add the Original Repository as a Remote

```bash
git remote add upstream https://github.com/confy-security/cli.git
git remote -v  # Verify you have 'origin' and 'upstream'
```

### 4. Install Dependencies with Poetry

```bash
poetry install
```

This command will:

- Create a virtual environment (if it doesn't exist)
- Install all main and development dependencies
- Automatically activate the virtual environment

### 5. Activate the Virtual Environment

If the environment was not activated automatically:

```bash
poetry shell
```

Or execute commands within the environment with:

```bash
poetry run <command>
```

## Project Structure

```txt
cli/
├── .github/
│   ├── CODEOWNERS              # Code owners
│   ├── dependabot.yml          # Dependabot configuration
│   └── workflows/
│       └── test.yml            # Test pipeline
├── confy_cli/
│   ├── __init__.py             # Main package
│   ├── main.py                 # Main CLI entry point
│   ├── settings.py             # Configuration management
│   ├── utils.py                # Utility functions
│   └── core/
│       ├── __init__.py
│       └── constants.py        # Project constants
├── .env.example                # Environment variables example
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Poetry and project config
├── poetry.lock                 # Dependency lock file
├── CONTRIBUTING.md             # This file
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── README.md
└── LICENSE
```

## Contribution Workflow

### 1. Create a Branch for Your Changes

Always create a separate branch for each contribution:

```bash
# Update from the main branch
git checkout main
git pull upstream main

# Create and switch to a new branch
git checkout -b type/short-description

# Example branch names:
# - feature/add-message-encryption
# - bugfix/fix-websocket-connection
# - docs/improve-readme
# - test/add-cli-tests
```

**Branch naming conventions:**

- `feature/` - For new features
- `bugfix/` - For bug fixes
- `docs/` - For documentation improvements
- `test/` - For adding/improving tests
- `refactor/` - For code refactoring

### 2. Make Your Changes

Make changes to the code following the project standards (see [Code Standards](#code-standards) section).

```bash
# Edit files as needed
vim confy_cli/main.py

# See the status of changes
git status

# Stage changes
git add .
```

### 3. Commit with Clear Messages

Write descriptive commit messages:

```bash
git commit -m "Add message signing functionality"
```

**Best practices for commit messages:**

- Use the imperative mood ("add" instead of "added")
- Start with a capital letter
- Don't use a period at the end
- Limit the first line to 50 characters
- Add a more detailed description after a blank line if needed

**Complete example:**

```txt
Fix WebSocket connection timeout issue

- Increase default connection timeout
- Add exponential backoff retry logic
- Improve error messages
```

## Code Standards

The Confy CLI project follows rigorous quality and style standards. Understanding these standards is essential.

### Style and Formatting - Ruff

The project uses **Ruff** for static analysis and code formatting.

**Active rules:**

- `I` - Import sorting
- `F` - Pyflakes errors
- `E` - PEP 8 style errors
- `W` - PEP 8 style warnings
- `PL` - Pylint
- `PT` - Pytest
- `D` - Docstrings (Pydocstyle)
- `UP` - Syntax updates
- `PERF` - Performance optimizations

**Main configurations:**

- Maximum line length: **99 characters**
- Quote style: **Single quotes** (`'`)
- Preview: Enabled (uses experimental Ruff features)

### Style Examples

**✅ Correct:**

```python
"""Module docstring explaining the module."""

import asyncio
from typing import Final

import typer
from confy_addons import AESEncryption

from confy_cli.settings import get_settings

TIMEOUT: Final[int] = 30


class MessageHandler:
    """Handle encrypted message operations."""

    def __init__(self, key: bytes) -> None:
        """Initialize message handler.

        Args:
            key: The encryption key.

        Raises:
            TypeError: If key is not bytes.

        """
        if not isinstance(key, bytes):
            raise TypeError('key must be bytes')
        self._key = key

    async def encrypt_message(self, plaintext: str) -> str:
        """Encrypt a plaintext message.

        Args:
            plaintext: The text to encrypt.

        Returns:
            str: The encrypted message in base64.

        """
        aes = AESEncryption(self._key)
        return aes.encrypt(plaintext)
```

**❌ Incorrect:**

```python
# Missing module docstring
import asyncio
import typer
from confy_addons import AESEncryption  # Wrong order
from confy_cli.settings import get_settings

TIMEOUT = 30  # No type hint

class MessageHandler:
    # Missing class docstring

    def __init__(self, key: bytes) -> None:  # Missing method docstring
        if not isinstance(key, bytes):
            raise TypeError("key must be bytes")  # Double quotes
        self._key = key

    async def encrypt_message(self, plaintext: str) -> str:  # Missing docstring
        aes = AESEncryption(self._key)
        return aes.encrypt(plaintext)
```

### Type Hints

Use type hints in all public methods:

```python
async def receive_messages(websocket) -> None:
    """Receive and process incoming messages."""
    ...

def get_protocol(url: str) -> tuple[str, str]:
    """Determine WebSocket protocol from URL."""
    ...

@property
def is_connected(self) -> bool:
    """Return connection status."""
    return self._connected
```

### Docstrings

Follow the **Google Style** standard for docstrings:

```python
async def send_message(self, message: str, recipient_id: str) -> None:
    """Send an encrypted message to a recipient.

    Encrypts the message using the established AES key and sends it
    through the WebSocket connection.

    Args:
        message: The plaintext message to send.
        recipient_id: The ID of the recipient.

    Raises:
        ValueError: If AES key is not established.
        websockets.ConnectionClosed: If connection is closed.

    """
```

### Constants

Use constants for magic values (already defined in `confy_cli/core/constants.py`):

```python
from confy_cli.core.constants import RAW_PAYLOAD_LENGTH

# ✅ Correct
payload_parts = raw_payload.split('::')
if len(payload_parts) != RAW_PAYLOAD_LENGTH:
    raise ValueError('Invalid payload format')

# ❌ Incorrect
if len(payload_parts) != 2:  # Magic number!
    raise ValueError('Invalid payload format')
```

### Logging and Debug Output

Use the utility functions from `confy_cli.utils` for consistent output:

```python
from confy_cli.utils import debug, alert, received

# Debug output (only if DEBUG=true)
debug('Connected to peer')

# Alert message
alert('Waiting for recipient to connect...')

# Received message
received('Hello, World!')
```

## Quality Tools

The project uses several tools to ensure quality. All are automatically executed by GitHub Actions.

### Ruff - Code Analysis and Formatting

**Check code:**

```bash
poetry run ruff check .
```

**Format code automatically:**

```bash
poetry run ruff format .
poetry run ruff check . --fix
```

### MyPy - Type Checking

Checks the correctness of type hints:

```bash
poetry run mypy -p confy_cli --ignore-missing-imports
```

**Example of detected error:**

```python
# MyPy will complain about this:
result: int = await async_function()  # Type mismatch
```

### Radon - Code Complexity

Analyzes cyclomatic complexity:

```bash
poetry run radon cc ./confy_cli -a -na
```

**A** = average | **NA** = non-aggregated (shows details per function)

### Bandit - Security

Checks for security issues:

```bash
poetry run bandit -r ./confy_cli
```

## Running the Project Locally

### Pre-development Checks

Run all quality checks before committing:

```bash
# Check code style
poetry run ruff check .

# Format code
poetry run ruff format .

# Type checking
poetry run mypy -p confy_cli --ignore-missing-imports

# Security check
poetry run bandit -r ./confy_cli

# Code complexity
poetry run radon cc ./confy_cli -a -na
```

### Complete Development Cycle

```bash
# 1. Create and switch to feature branch
git checkout -b feature/my-feature

# 2. Make changes to the code
vim confy_cli/main.py

# 3. Format and check code
poetry run ruff format .
poetry run ruff check . --fix

# 4. Run type checking
poetry run mypy -p confy_cli --ignore-missing-imports

# 5. Run security checks
poetry run bandit -r ./confy_cli

# 6. If all passes, stage and commit
git add .
git commit -m "Add new feature"

# 7. Push to your fork
git push origin feature/my-feature
```

## Testing the CLI

Test your changes manually:

```bash
# Build and install the package locally
poetry install

# Run the CLI
poetry run confy my-user-id recipient-id

# Or if installed globally
confy my-user-id recipient-id
```

### Troubleshooting

Error: Poetry not found

```bash
pip install poetry
poetry --version
```

Error: Virtual environment not activated

```bash
poetry shell
# or use 'poetry run' before each command
```

Error: WebSocket connection fails

Check that:

1. The server address is correct
2. The server is running and accessible
3. User IDs are valid and exist on the server
4. Network connectivity is available

## Creating a Pull Request

### 1. Update with the Main Branch

Before pushing, synchronize with the main branch:

```bash
git fetch upstream
git rebase upstream/main
```

If there are conflicts, resolve them and continue:

```bash
git add .
git rebase --continue
```

### 2. Push to Your Fork

```bash
git push origin feature/your-feature
```

### 3. Create the Pull Request

1. Go to your fork on GitHub
2. You will see a "Compare & pull request" suggestion
3. Click and fill in the PR template

**PR Template:**

```markdown
## 📝 Description

Brief and clear description of what was changed and why.

## 🎯 Type of Change

- [ ] Bug fix (fix that doesn't break existing functionality)
- [ ] New feature (adds functionality that doesn't break existing features)
- [ ] Breaking change (alters existing functionality)
- [ ] Documentation
- [ ] Code refactoring

## 🔍 Checklist

- [ ] I ran `poetry run ruff format .` and the code is formatted
- [ ] I ran `poetry run ruff check .` and there are no errors
- [ ] I ran `poetry run mypy -p confy_cli` and there are no type errors
- [ ] I ran `poetry run bandit -r ./confy_cli` and there are no security issues
- [ ] I ran `poetry run radon cc ./confy_cli -a -na` and complexity is acceptable
- [ ] I tested the changes manually
- [ ] I updated documentation if necessary
- [ ] My PR has no conflicts with the main branch

## 🖼️ Testing (if applicable)

Describe how you tested these changes or any special testing considerations.

## 📚 References

Links to related issues or relevant documentation.

Closes #123
```

### 4. Respond to Reviews

Keep the conversation professional and constructive:

- Answer all questions from reviewers
- Make requested changes with new commits
- If you disagree, explain your viewpoint educatedly
- Ask for clarification if you don't understand

## Review Process

### What We Expect

1. **Code follows standards** - Ruff, MyPy, Bandit, Radon
2. **Quality checks pass** - All automated tests must pass
3. **Documentation updated** - Docstrings updated if needed
4. **Well-structured commits** - Clear and atomic messages
5. **No breaking changes** - Unless explicitly intended

### Review Cycle

1. Submit the PR
2. Automated tests run in CI/CD (GitHub Actions)
3. Team members review the code
4. Changes are requested (if necessary)
5. You make adjustments and push new commits
6. After approval, the PR is merged

### Respectful Conversation

- Receive feedback as a learning opportunity
- Review others' code constructively
- Use professional and courteous tone
- Focus on the code, not the person

## Reporting Security Issues

⚠️ **DO NOT** report vulnerabilities in public issues.

To report a security vulnerability:

1. **Send an email to:** [confy@henriquesebastiao.com](mailto:confy@henriquesebastiao.com)
2. **Include:**
   - Detailed description of the issue
   - Steps to reproduce
   - Code example if possible
   - Affected version

The team will respond within 48 hours. See [SECURITY.md](SECURITY.md) for more details.

## Frequently Asked Questions

### How do I get started?

1. Fork the repository
2. Clone your fork
3. Create a branch (`git checkout -b feature/my-feature`)
4. Make changes and commits
5. Push to your fork
6. Create a Pull Request

### Which Python version should I use?

Use **Python 3.13 or higher** for development. The project requires Python 3.13+.

### How do I set up the development environment quickly?

```bash
git clone https://github.com/YOUR-USERNAME/cli.git
cd cli
poetry install
poetry shell
```

### Can I test the CLI without a server?

You need a running Confy server to test the CLI. You can:

1. Set up the server locally
2. Connect to a test server if available
3. Contribute to the server project as well

### What if my code is too complex?

Run Radon to check complexity:

```bash
poetry run radon cc ./confy_cli -a -na
```

Refactor if necessary. PRs with very high complexity may be rejected.

### What does each Ruff rule mean?

Check the [Ruff documentation](https://docs.astral.sh/ruff/).

### How can I contribute without coding?

You can help by:

- Reporting bugs
- Improving documentation
- Translating documentation
- Testing the CLI
- Sharing ideas for features

## Useful Resources

- 🔧 [Ruff Documentation](https://docs.astral.sh/ruff/)
- 📚 [Poetry Documentation](https://python-poetry.org/docs/)
- 🔐 [Cryptography Library](https://cryptography.io/)
- 📡 [Websockets Library](https://websockets.readthedocs.io/)
- 🎯 [Typer Documentation](https://typer.tiangolo.com/)

## Thank You!

Your contribution makes this project better. If you have questions, open an issue or contact us through the email above.

**Built with ❤️ by Brazilian students**