# Test Organization

## Summary

Reorganized test files from scattered locations into a structured test directory hierarchy.

## Changes Made

### Directory Structure

**Before:**
```
├── test_parser_improvements.py    # Root directory
├── tests/
│   ├── test_basic.py
│   └── test_ingredient_parsing.py
└── scripts/
    ├── test_fixes.py
    ├── test_new_failures.py
    ├── test_uuid_filename.py
    ├── test_schedule.py
    └── processing/
        ├── test_comprehensive_parsing.py
        └── test_csv_performance.py
```

**After:**
```
tests/
├── README.md                 # Documentation
├── unit/                     # Fast, isolated tests
│   ├── test_basic.py
│   ├── test_ingredient_parsing.py
│   ├── test_parser_improvements.py
│   └── test_uuid_filename.py
├── integration/              # Tests requiring services
│   ├── test_data_loading_fixes.py
│   ├── test_ingredient_filtering.py
│   └── test_temporal_schedule.py
└── scripts/                  # Standalone test scripts
    ├── test_comprehensive_parsing.py
    └── test_csv_performance.py
```

### Files Moved

| Old Location | New Location | Type |
|-------------|--------------|------|
| `test_parser_improvements.py` | `tests/unit/test_parser_improvements.py` | Unit test |
| `scripts/test_fixes.py` | `tests/integration/test_data_loading_fixes.py` | Integration test |
| `scripts/test_new_failures.py` | `tests/integration/test_ingredient_filtering.py` | Integration test |
| `scripts/test_uuid_filename.py` | `tests/unit/test_uuid_filename.py` | Unit test |
| `scripts/test_schedule.py` | `tests/integration/test_temporal_schedule.py` | Integration test |
| `tests/test_basic.py` | `tests/unit/test_basic.py` | Unit test |
| `tests/test_ingredient_parsing.py` | `tests/unit/test_ingredient_parsing.py` | Unit test |
| `scripts/processing/test_comprehensive_parsing.py` | `tests/scripts/test_comprehensive_parsing.py` | Script |
| `scripts/processing/test_csv_performance.py` | `tests/scripts/test_csv_performance.py` | Script |

### Path Fixes

All moved files were updated with correct import paths:
```python
# Updated from various paths to:
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
```

### New Files

- `tests/README.md` - Comprehensive test documentation
- `tests/unit/__init__.py` - Python package marker
- `tests/integration/__init__.py` - Python package marker
- `tests/scripts/__init__.py` - Python package marker

## Running Tests

### All Unit Tests
```bash
pytest tests/unit/ -v
```

### All Integration Tests
```bash
# Requires services running
docker-compose up -d
pytest tests/integration/ -v
```

### Specific Test
```bash
pytest tests/unit/test_uuid_filename.py -v
```

### All Tests
```bash
pytest tests/ -v
```

## Benefits

1. ✅ **Clear Organization**: Tests grouped by type (unit/integration/scripts)
2. ✅ **Easy Navigation**: Logical structure makes tests easy to find
3. ✅ **Better Discovery**: pytest can easily discover all tests
4. ✅ **Documentation**: README explains test structure and usage
5. ✅ **Scalability**: Easy to add new tests in appropriate categories

## Test Categories

### Unit Tests (`tests/unit/`)
- Fast, isolated tests
- No external dependencies
- Test individual functions/classes
- Run frequently during development

### Integration Tests (`tests/integration/`)
- Test component interactions
- Require database, Temporal, etc.
- Test workflows and activities
- Run before commits/deploys

### Script Tests (`tests/scripts/`)
- Standalone test utilities
- Manual/debugging tests
- Performance benchmarks
- Not part of automated test suite

## CI/CD Integration

Tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run unit tests
  run: pytest tests/unit/ -v

- name: Run integration tests
  run: |
    docker-compose up -d
    pytest tests/integration/ -v
```

## Future Improvements

- [ ] Migrate legacy JS tests to Python
- [ ] Add E2E tests for full pipeline
- [ ] Add performance tests
- [ ] Set up coverage reporting
- [ ] Add pre-commit hooks for tests

