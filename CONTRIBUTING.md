# Contributing to Nebula Search

Thank you for your interest in contributing! This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## How to Contribute

### 1. Set Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Sky-254-1/NEBULA-SEARCH-.git
cd NEBULA-SEARCH-

# Run quick start script
bash scripts/quick-start.sh

# Or using Make
make install
make dev
```

### 2. Find or Create an Issue

- Check existing issues on GitHub
- For new features, create an issue first to discuss the approach
- For bug fixes, reference the bug report

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### 4. Make Changes

Follow these guidelines:

#### Code Style

**Python (Backend):**
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use async/await for I/O operations
- Write docstrings for all public functions/classes

**TypeScript (Frontend):**
- Use functional components with hooks
- Prefer `const` over `let`
- Use descriptive variable names
- Write JSDoc comments for complex functions

#### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(search): add vector search support
fix(auth): resolve JWT token expiration issue
docs(readme): update installation instructions
```

### 5. Write Tests

All new features should include tests:

**Backend (pytest):**
```bash
# Run all tests
make test

# Run specific test file
pytest backend/tests/test_documents_routes.py -v

# Run with coverage
pytest --cov=backend --cov-report=html
```

**Frontend (Vitest):**
```bash
# Run all tests
cd frontend
npm test

# Run with coverage
npm run test:coverage
```

### 6. Run Linters

```bash
# Backend linting
cd backend
ruff check .
mypy .

# Frontend linting
cd frontend
npm run lint
npm run type-check
```

### 7. Submit Pull Request

1. Push your branch to GitHub
2. Create a Pull Request against `main` branch
3. Fill out the PR template
4. Ensure CI checks pass
5. Request review from maintainers

## Development Guidelines

### Architecture

- **Backend**: FastAPI with async/await patterns
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis (optional, falls back to in-memory)
- **Search**: Elasticsearch for vector search (optional)
- **Storage**: Local filesystem or S3/MinIO

### Project Structure

```
backend/
├── app/
│   ├── middleware/     # Security, rate limiting, etc.
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   ├── models/         # Database models
│   └── main.py         # Application entry
├── tests/              # Test suite
└── requirements.txt    # Dependencies

frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── context/        # React contexts
│   ├── api/            # API client
│   └── utils/          # Utility functions
└── package.json        # Dependencies
```

### Database Migrations

When changing database models:

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### API Design

- Use RESTful conventions
- Version APIs (`/api/v1/...`)
- Return consistent JSON responses
- Use proper HTTP status codes
- Document with OpenAPI/Swagger

### Error Handling

- Use custom exception classes
- Log errors with context
- Return user-friendly error messages
- Never expose internal details to users

### Security

- Always validate user input
- Use parameterized queries (prevent SQL injection)
- Implement proper authentication/authorization
- Never log sensitive data (passwords, tokens)
- Use HTTPS in production
- Set security headers

## Testing Strategy

### Backend Tests

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test API endpoints
3. **E2E Tests**: Test complete user flows

### Frontend Tests

1. **Unit Tests**: Test utility functions and components
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test user workflows with Playwright

## Performance

- Use database indexes for frequently queried fields
- Implement caching for expensive operations
- Use connection pooling for databases
- Compress API responses
- Optimize database queries (avoid N+1 problems)

## Documentation

- Update README.md for major changes
- Add docstrings to new functions/classes
- Update API documentation (auto-generated from code)
- Add examples for complex features

## Review Process

1. **Automated Checks**: CI must pass (tests, linting, type checking)
2. **Code Review**: At least one maintainer must approve
3. **Testing**: New features must have tests
4. **Documentation**: Changes must be documented

## Getting Help

- Open an issue for bugs or feature requests
- Check documentation in `docs/` folder
- Review existing code for examples
- Ask questions in GitHub Discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.