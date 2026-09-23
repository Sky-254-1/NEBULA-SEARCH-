# Contributing to Nebula Search

Thank you for your interest in contributing to Nebula Search! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 20 or higher
- Git
- Docker (optional, for full stack testing)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Nebula-search-engine-.git
   cd Nebula-search-engine-
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/Sky-254-1/Nebula-search-engine-.git
   ```

### Local Setup

See [docs/SETUP.md](SETUP.md) for detailed setup instructions.

**Quick start:**

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Frontend
cd ../frontend
npm install

# Run tests
cd ../backend
pytest
```

## Development Workflow

### Branch Strategy

- `main` — stable production code
- `develop` — integration branch for features
- `feature/name` — new features
- `fix/name` — bug fixes
- `docs/name` — documentation updates

### Creating a Feature Branch

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

### Keeping Your Fork Updated

```bash
git fetch upstream
git checkout develop
git merge upstream/develop
git push origin develop
```

## Coding Standards

### Python (Backend)

- **Style:** Follow PEP 8
- **Formatter:** Black (line length: 100)
- **Linter:** Ruff
- **Type hints:** Use type annotations where possible
- **Docstrings:** Google style

**Run formatters:**
```bash
black backend/app
ruff check backend/app --fix
```

**Example:**
```python
async def search_documents(
    query: str,
    user_id: int,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search documents for a user.

    Args:
        query: Search query string
        user_id: User ID for scoping
        limit: Maximum number of results

    Returns:
        List of document dictionaries with scores

    Raises:
        ValueError: If query is empty
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Implementation
    return results
```

### JavaScript/React (Frontend)

- **Style:** Prettier with 2-space indentation
- **Linter:** ESLint
- **Components:** Functional components with hooks
- **Props:** Use PropTypes or TypeScript

**Run formatters:**
```bash
cd frontend
npm run lint
npm run format
```

**Example:**
```javascript
export function SearchBar({ value, onChange, onSubmit, loading }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      onSubmit();
    }
  };

  return (
    <div className="search-bar">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={loading}
        placeholder="Search..."
      />
    </div>
  );
}
```

## Testing Guidelines

### Backend Tests

- **Framework:** pytest + pytest-asyncio
- **Coverage:** Minimum 80% (enforced by CI)
- **Location:** `tests/` directory

**Run tests:**
```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

**Test structure:**
```python
import pytest
from app.services.search import sanitize_query

@pytest.mark.asyncio
async def test_sanitize_query_removes_control_chars():
    """Ensure control characters are stripped from queries."""
    result = sanitize_query("hello\x00world\x1f")
    assert result == "helloworld"

def test_sanitize_query_normalizes_whitespace():
    """Ensure multiple spaces are normalized."""
    result = sanitize_query("hello    world")
    assert result == "hello world"
```

### Frontend Tests

- **Framework:** Jest + React Testing Library
- **Coverage:** Minimum 70%

**Run tests:**
```bash
cd frontend
npm test
npm run test:coverage
```

### E2E Tests

- **Framework:** Playwright
- **Location:** `tests/e2e/`

**Run E2E:**
```bash
npm run e2e
npm run e2e:ui  # Interactive mode
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(search): add semantic search with embeddings

Implement sentence-transformers integration for vector search.
Chunks are now embedded with all-MiniLM-L6-v2 model and stored
in FAISS index for similarity search.

Closes #42
```

```
fix(auth): prevent token reuse after refresh

Session rotation was not being marked correctly, allowing
refresh tokens to be reused multiple times.

Fixes #89
```

## Pull Request Process

### Before Submitting

1. **Update your branch:**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. **Run all tests:**
   ```bash
   pytest
   npm test
   npm run e2e
   ```

3. **Run linters:**
   ```bash
   black backend/app
   ruff check backend/app
   npm run lint
   ```

4. **Update documentation** if needed

5. **Add tests** for new features

### Submitting

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub

3. Fill out the PR template:
   - **Title:** Clear, descriptive (use conventional commit format)
   - **Description:** What changed and why
   - **Testing:** How you tested the changes
   - **Screenshots:** For UI changes
   - **Breaking changes:** List any breaking changes

### PR Review Process

- **Automated checks** must pass (CI/CD, tests, linting)
- **Code review** by at least one maintainer
- **Changes requested:** Address feedback and push updates
- **Approval:** Once approved, a maintainer will merge

### After Merge

1. Delete your feature branch (locally and on GitHub)
2. Update your local develop branch:
   ```bash
   git checkout develop
   git pull upstream develop
   ```

## Documentation

### Updating Docs

- **API changes:** Update `docs/API_V1.1.md`
- **Architecture changes:** Update `docs/ARCHITECTURE.md`
- **Setup instructions:** Update `docs/SETUP.md`
- **New features:** Update `README.md` and relevant docs

### Writing Docs

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Keep formatting consistent

## Questions?

- **Bugs:** Open an issue with the `bug` label
- **Features:** Open an issue with the `enhancement` label
- **Questions:** Open a discussion on GitHub Discussions
- **Security:** Email security@nebula-search.example.com (do not open public issues)

Thank you for contributing to Nebula Search! 🚀
