# Tests Directory - LUMEN Library Management System

This directory contains all automated tests for validating the character limits implementation and dynamic features.

## Test Files

### Character Limits Tests
- **`test_character_limits.py`** - Comprehensive character limits validation
- **`validate_limits.py`** - Quick validation script for all field limits

### Dynamic Features Tests  
- **`test_dynamic_year.py`** - Tests dynamic year calculation for book forms
- **`test_dynamic_copies.py`** - Tests dynamic copy limits for book forms (if created)

## Running Tests

```bash
# Run individual tests
python tests/test_character_limits.py
python tests/test_dynamic_year.py  
python tests/validate_limits.py

# Or run from project root
./venv/Scripts/python.exe tests/test_character_limits.py
./venv/Scripts/python.exe tests/test_dynamic_year.py
./venv/Scripts/python.exe tests/validate_limits.py
```

## What These Tests Validate

✅ **Model character limits are correctly implemented**  
✅ **Form validation works with new limits**  
✅ **Dynamic year calculation functions properly**  
✅ **Dynamic copy limits are enforced**  
✅ **All field constraints are properly set**