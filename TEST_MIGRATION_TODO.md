# Test Migration for Async Services

## Status

The service layer methods have been converted to async, but the tests still use synchronous database sessions and fixtures. This causes test failures because async methods are being called without `await`.

## Failing Tests (19 total)

### test_chat.py
- test_get_chat_messages
- test_clear_chat_messages

### test_insights.py
- test_save_and_get_insight_with_same_text
- test_different_text_same_reference_not_cached
- test_get_all_insights
- test_clear_all_insights

### test_translation_references.py
- test_insight_with_translation_in_reference
- test_different_translations_cached_separately
- test_standalone_chat_with_translation_in_reference
- test_user_insights_with_multiple_translations

### test_device_link.py
- test_merge_users_data_transfer
- test_merge_users_no_duplicate_insights
- test_full_device_linking_workflow

### test_user.py
- test_clear_user_data
- test_export_user_data
- test_import_user_data
- test_user_data_segregation_insights
- test_user_data_segregation_chats
- test_insight_caching_across_users

## Solution

Two approaches:

### Option 1: Async Test Fixtures (Recommended)
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

## Recommendation

Implement **Option 1** properly:

1. Add `pytest-asyncio` to `requirements-test.txt`
2. Create async fixtures in `conftest.py`
3. Mark affected tests with `@pytest.mark.asyncio`
4. Update test method signatures to `async def`
5. Add `await` to all service method calls

This ensures tests properly exercise the async code paths and database operations.

## Timeline

- **Short term**: Skip/mark failing tests to unblock PR merge
- **Medium term**: Implement async test fixtures and update all affected tests
- **Long term**: All tests should use async patterns once full migration is complete
