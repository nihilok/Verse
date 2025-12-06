# Async Database Operations Migration

## Problem
Currently using synchronous SQLAlchemy sessions (`Session`) throughout the application. With a single uvicorn worker, synchronous database operations block the event loop, preventing the server from handling other requests while waiting for database I/O.

## Solution
Migrate to SQLAlchemy's async session support (`AsyncSession`) to allow non-blocking database operations.

## Current State Audit

### Synchronous DB Operations Found

**bible_service.py** (2 sync methods):
- `save_passage(db: Session, ...)`

**chat_service.py** (4 sync methods):
- `get_chat_messages(db: Session, ...)`
- `clear_chat_messages(db: Session, ...)`
- `get_standalone_chats(db: Session, ...)`
- `delete_standalone_chat(db: Session, ...)`

**definition_service.py** (3 sync methods):
- `link_definition_to_user(db: Session, ...)`
- `get_user_definitions(db: Session, ...)`
- `clear_user_definitions(db: Session, ...)`

**device_link_service.py** (5 sync methods):
- `generate_link_code(db: Session, ...)`
- `merge_users(db: Session, ...)`
- `get_user_devices(db: Session, ...)`
- `unlink_device(db: Session, ...)`
- `cleanup_expired_codes(db: Session, ...)`
- `revoke_user_codes(db: Session, ...)`

**insight_service.py** (3 sync methods):
- `link_insight_to_user(db: Session, ...)`
- `get_user_insights(db: Session, ...)`
- `clear_user_insights(db: Session, ...)`

**user_service.py** (5 sync methods):
- `get_or_create_user(db: Session, ...)`
- `get_user_by_anonymous_id(db: Session, ...)`
- `_link_insight_to_user(db: Session, ...)`
- `clear_user_data(db: Session, ...)`
- `export_user_data(db: Session, ...)`
- `import_user_data(db: Session, ...)`

**Total: 23+ synchronous database methods**

## Migration Steps

### 1. Update Database Configuration (`app/core/database.py`)
- Add `AsyncEngine` using `create_async_engine`
- Create `async_sessionmaker` for async sessions
- Update `get_db()` to async generator with automatic transaction management:
  - Yields `AsyncSession`
  - Automatically commits on success
  - Automatically rolls back on exception
- Keep sync engine for migration scripts (Alembic)

### 2. Update Service Methods
Convert all synchronous database methods to async:
- Change `def` → `async def`
- Change `Session` → `AsyncSession`
- Replace `.query()` style with SQLAlchemy 2.0 async style:
  - `db.query()` → `await db.execute(select(...))`
  - `db.add()` → `db.add()` (still sync)
  - **Remove `db.commit()` calls** - automatic via `get_db()` dependency
  - `db.refresh()` → `await db.refresh()`
  - `db.flush()` → `await db.flush()` (when you need generated IDs before commit)
  - `db.delete()` → followed by transaction auto-commit

### 3. Update API Routes (`app/api/routes.py`)
- Update all route handlers to use `async def`
- Update `db: Session = Depends(get_db)` → `db: AsyncSession = Depends(get_db)`
- Add `await` to all service method calls

### 4. Update Query Patterns
Replace SQLAlchemy 1.x style queries with 2.0 async style:

**Before:**
```python
db.query(Model).filter(Model.id == id).first()
```

**After:**
```python
from sqlalchemy import select
result = await db.execute(select(Model).where(Model.id == id))
model = result.scalar_one_or_none()
```

### 5. Testing
- Update tests to use `AsyncSession`
- Test all endpoints with async database operations
- Verify no blocking operations remain

## Benefits
- Non-blocking I/O allows single worker to handle multiple concurrent requests
- Better resource utilization
- Improved response times under load
- Follows FastAPI best practices for async operations

## Risks & Mitigations
- **Risk:** Large change touching many files
  - **Mitigation:** Work in feature branch, thorough testing
- **Risk:** Breaking existing functionality
  - **Mitigation:** Comprehensive test coverage, gradual rollout
- **Risk:** Alembic migrations may need sync engine
  - **Mitigation:** Keep sync engine available for migrations

## Dependencies
- SQLAlchemy 2.0+ (already installed: >=2.0.36)
- asyncpg for PostgreSQL (need to add)
- aiosqlite for SQLite testing (already installed: >=0.19.0)
