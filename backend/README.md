# Python FastAPI Boilerplate

A production-ready FastAPI boilerplate with best practices and common features.

## Features

- FastAPI framework
- SQLAlchemy ORM with database migrations
- Redis integration
- AWS S3 integration
- Email service
- Session management
- Authentication and authorization
- Logging system
- CI/CD workflows
- Code quality tools

## Setup

1. Clone the repository
2. Install dependencies:

   ```bash
   poetry install
   ```

3. Copy `.env-sample` to `.env` and configure your environment variables

4. Run migrations:

   ```bash
   alembic revision --autogenerate -m 'initials'
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   poetry run uvicorn asgi:app --reload
   ```

## Project Structure

```
python-fastapi-boilerplate/
├── apps/          # Application code
├── config/        # Configuration files
├── core/          # Core utilities and helpers
├── middleware/    # Custom middleware
├── assets/        # Static files and templates
└── log_service/   # Logging service
```

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint code: `flake8`
- Type check: `mypy .`

## License

MIT
