# Tests Directory

Organized test suite for the Recipes ETL project.

## Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_basic.py
│   ├── test_ingredient_parsing.py
│   ├── test_parser_improvements.py
│   └── test_uuid_filename.py
│
├── integration/             # Integration tests (requires DB, Temporal)
│   ├── test_data_loading_fixes.py
│   ├── test_ingredient_filtering.py
│   └── test_temporal_schedule.py
│
├── scripts/                 # Standalone test scripts
│   ├── test_comprehensive_parsing.py
│   └── test_csv_performance.py
│
├── models/                  # Legacy JS tests (to be migrated)
│   └── Recipe.test.js
│
├── schemas/                 # Legacy JS tests (to be migrated)
│   └── recipe-schema.test.js
│
└── services/                # Legacy JS tests (to be migrated)
    └── AIService.test.js
```

## Running Tests

### Unit Tests (Fast)
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test
pytest tests/unit/test_basic.py -v
pytest tests/unit/test_uuid_filename.py -v
```

### Integration Tests (Requires Services)
```bash
# Start required services first
docker-compose up -d

# Run all integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/integration/test_temporal_schedule.py -v
```

### All Tests
```bash
# Run entire test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/recipes --cov-report=html
```

### Standalone Scripts
```bash
# These are manual test scripts, run directly
python tests/scripts/test_comprehensive_parsing.py
python tests/scripts/test_csv_performance.py
```

## Test Categories

### Unit Tests
- **test_basic.py**: Basic setup and configuration tests
- **test_ingredient_parsing.py**: Ingredient parser unit tests
- **test_parser_improvements.py**: Recipe parser validation tests
- **test_uuid_filename.py**: UUID generation and filename tests

### Integration Tests
- **test_data_loading_fixes.py**: Tests for data loading fixes (Stromberg, Reddit)
- **test_ingredient_filtering.py**: Tests for ingredient filtering enhancements
- **test_temporal_schedule.py**: Temporal schedule verification tests

### Script Tests
- **test_comprehensive_parsing.py**: Manual parsing tests for debugging
- **test_csv_performance.py**: Performance benchmarking for CSV processing

## Writing New Tests

### Unit Test Template
```python
#!/usr/bin/env python3
"""Description of what this tests."""

import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.utils.something import something

def test_something():
    """Test description."""
    result = something()
    assert result is not None
```

### Integration Test Template
```python
#!/usr/bin/env python3
"""Description of integration test."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.workflows.activities import some_activity

async def test_integration():
    """Test description."""
    result = await some_activity()
    assert result['success'] is True

if __name__ == '__main__':
    asyncio.run(test_integration())
```

## Test Conventions

1. **File Naming**: `test_*.py` for all test files
2. **Function Naming**: `test_*` for pytest test functions
3. **Async Tests**: Use `asyncio.run()` or pytest-asyncio
4. **Imports**: Always add project root to path for imports
5. **Documentation**: Include docstrings for all test functions

## CI/CD

Tests are run automatically on:
- Push to main
- Pull requests
- Pre-commit hooks (unit tests only)

## Migration TODO

- [ ] Migrate JS tests to Python (models/, schemas/, services/)
- [ ] Add more unit tests for services
- [ ] Add integration tests for workflows
- [ ] Add E2E tests for full pipeline

