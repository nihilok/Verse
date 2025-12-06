# Test Migration for Async Services

## Status

**Current: 139/154 tests passing (90%)**

The async database migration is largely complete with async test fixtures working. Remaining 15 failures are due to incomplete service layer migrations.

## Remaining Failures (15 total)

### Fixed ✅
- test_chat.py: All passing after adding greenlet dependency
- test_insights.py: All passing
- test_translation_references.py: All passing

### test_insights.py
- test_save_and_get_insight_with_same_text
- test_different_text_same_reference_not_cached
- test_get_all_insights
- test_clear_all_insights

### test_streaming.py (9 failures)
- All streaming test failures are due to ChatMessage not being persisted
- Root cause: Transaction handling in async context with streaming responses
- Need to investigate flush/commit timing in streaming scenarios

### test_device_link.py (3 failures)
- test_merge_users_data_transfer - DeviceLinkService.merge_users() not yet async
- test_merge_users_no_duplicate_insights - DeviceLinkService.merge_users() not yet async
- test_full_device_linking_workflow - DeviceLinkService.generate_link_code(), validate_and_use_code() not yet async

### test_user.py (3 failures)
- test_clear_user_data - Missing await on db.execute() in user_service.clear_user_data()
- test_export_user_data - UserService methods need full async conversion
- test_import_user_data - UserService.import_user_data() transaction handling needs fixing

## Fixes Applied

### Async Test Fixtures ✅
Implemented in conftest.py:
Add async database session support to `conftest.py`:

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Create async test engine
async_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False}
)

AsyncTestingSessionLocal = async_sessionmaker(
    async_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest_asyncio.fixture
async def async_db():
    """Create an async database session for tests."""
    async with AsyncTestingSessionLocal() as session:
        yield session
        # Cleanup
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
```

Then update tests:
```python
@pytest.mark.asyncio
async def test_get_all_insights(async_db, test_user):
    service = InsightService()
    # ... setup ...
    insights = await service.get_user_insights(async_db, test_user.id)
    assert len(insights) == 2
```

### Option 2: Run Async Methods in Sync Context
Use `asyncio.run()` or `pytest-asyncio` to run async methods:

```python
import asyncio

def test_get_all_insights(db, test_user):
    service = InsightService()
    # Convert sync session to async context
    # This is hacky and not recommended
```

### Dependencies Added ✅
- Added `greenlet>=3.0.0` to pyproject.toml (required for async SQLAlchemy)

### Syntax Errors Fixed ✅
- Fixed misplaced docstrings in test_device_link.py and test_user.py
- Fixed missing UserService imports in several test functions

## Remaining Work

### 1. Complete Service Layer Async Migration
Services still needing async conversion for failing tests:
- `DeviceLinkService`: merge_users(), generate_link_code(), validate_and_use_code()
- `UserService`: Fix await statements in clear_user_data(), export_user_data(), import_user_data()

### 2. Fix Streaming Tests
- Investigate why ChatMessage objects aren't being persisted in async streaming context
- May need to adjust transaction/flush timing around streaming responses
- All 9 streaming tests have same root cause

### 3. Documentation Updates
- Backend now uses `pyproject.toml` with `uv` for dependency management
- Updated `.github/copilot-instructions.md` with correct commands
