# Async Database Migration - Current Status

## Completed (Step 1/3)

### Infrastructure Setup ✅
- Added `asyncpg>=0.29.0` dependency for PostgreSQL async operations
- Created `AsyncEngine` with `create_async_engine()` in `database.py`
- Created `AsyncSessionLocal` session maker
- Converted `get_db()` dependency to async generator
- Kept separate `sync_engine` for Alembic migrations (backwards compatibility)
- Updated `main.py` to dispose async engine on shutdown
- Started service migration with `bible_service.save_passage()`

## Remaining Work (Steps 2-3)

### Step 2: Service Layer Migration (22 methods remaining)

**Pattern for each method:**
1. Change `def method_name(self, db: Session, ...)` → `async def method_name(self, db: AsyncSession, ...)`
2. Replace `.query()` style with SQLAlchemy 2.0 `select()`:
   ```python
   # Old
   result = db.query(Model).filter(Model.id == id).first()

   # New
   from sqlalchemy import select
   result = await db.execute(select(Model).where(Model.id == id))
   model = result.scalar_one_or_none()
   ```
3. Add `await` to: `db.commit()`, `db.refresh()`, `db.execute()`
4. Keep `db.add()` and `db.delete()` as-is (not async)

**Services to migrate:**
- `chat_service.py`: 4 methods (get_chat_messages, clear_chat_messages, get_standalone_chats, delete_standalone_chat)
- `definition_service.py`: 3 methods (link_definition_to_user, get_user_definitions, clear_user_definitions)
- `device_link_service.py`: 6 methods (generate_link_code, merge_users, get_user_devices, unlink_device, cleanup_expired_codes, revoke_user_codes)
- `insight_service.py`: 3 methods (link_insight_to_user, get_user_insights, clear_user_insights)
- `user_service.py`: 6 methods (get_or_create_user, get_user_by_anonymous_id, _link_insight_to_user, clear_user_data, export_user_data, import_user_data)

### Step 3: API Route Layer Migration (27 endpoints)

All route handlers in `app/api/routes.py` need:
1. Update dependency: `db: Session = Depends(get_db)` → `db: AsyncSession = Depends(get_db)`
2. Add `await` to all service method calls that were converted to async
3. Verify all route handlers are `async def` (most already are)

## Testing Requirements

1. **Unit Tests**: Update test fixtures to use `AsyncSession`
2. **Integration Tests**: Verify all endpoints work with async operations
3. **Load Testing**: Confirm non-blocking behavior under concurrent load

## Branch & PR Strategy

- Branch: `feat/async-db-operations`
- Approach: Complete migration in this branch, create PR for review before merging
- Can be split into multiple commits for easier review:
  1. Infrastructure (✅ done)
  2. Service layer migration (in progress)
  3. Route layer migration
  4. Test updates

## Benefits

- **Non-blocking I/O**: Single uvicorn worker can handle multiple concurrent requests
- **Better resource utilization**: No thread/process overhead from blocking calls
- **Improved scalability**: Natural fit for FastAPI's async architecture
- **Future-proof**: Aligns with modern Python async best practices

## Risks & Mitigation

- **Large scope**: Many files touched
  - ✅ Mitigation: Systematic approach with checklist, thorough testing
- **Query pattern changes**: SQLAlchemy 1.x → 2.0 async style
  - ✅ Mitigation: Consistent patterns documented, can reference existing async methods
- **Breaking changes**: All service methods change signature
  - ✅ Mitigation: Type system will catch issues, comprehensive tests

## Next Steps

1. Continue with chat_service.py (most critical, 4 methods)
2. Move through other services systematically
3. Update all routes in single commit
4. Update and run test suite
5. Create PR with comprehensive description
