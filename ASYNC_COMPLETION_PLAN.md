# Async Migration - Completion Plan

## Current Status

**Service Layer: 100% Complete** ✅
All service methods with database operations have been converted to async.

**API Routes: 100% Complete** ✅
All routes now use `AsyncSession` instead of `Session`.

**Tests: ~50% Complete** ⚠️
- Async tests (using `async_db` fixture): Working
- Sync tests (using `db` fixture): Need conversion for methods that are now async

## Completed Service Methods

### DeviceLinkService
- ✅ generate_link_code()
- ✅ validate_and_use_code()
- ✅ merge_users()
- ✅ get_user_devices()
- ✅ unlink_device()
- ✅ create_or_update_device()
- ✅ cleanup_expired_codes()
- ✅ revoke_user_codes()

### UserService
- ✅ get_or_create_user()
- ✅ get_user_by_anonymous_id()
- ✅ clear_user_data()
- ✅ export_user_data()
- ✅ import_user_data()
- ✅ _link_insight_to_user()

### DefinitionService
- ✅ link_definition_to_user()
- ✅ get_saved_definition()
- ✅ get_user_definitions()
- ✅ clear_user_definitions()

### InsightService, ChatService, BibleService
- ✅ Already completed in previous commits

## Remaining Work: Test Conversion

### tests/test_device_link.py (9 sync tests to convert)

1. **test_generate_link_code** - Line 12
   - Change: `def test_generate_link_code(db, test_user):`
   - To: `@pytest.mark.asyncio\nasync def test_generate_link_code(async_db, async_test_user):`
   - Add `await` to: `service.generate_link_code()`
   - Change query to async select pattern

2. **test_generate_link_code_rate_limiting** - Line 37
   - Same pattern as above

3. **test_validate_and_use_code_success** - Line 50
   - Convert to async, use `create_test_user()` helper
   - Add `await` to all service calls

4. **test_validate_code_expired** - Line 80
   - Already has `@pytest.mark.asyncio` but check signature

5. **test_validate_code_already_used** - Line 109
   - Already has `@pytest.mark.asyncio` but verify completion

6. **test_merge_users_keeps_higher_device_count** - Line 222
   - Convert to async
   - Add `await` to `merge_users()`

7. **test_create_or_update_device** - Line 288
   - Convert to async
   - Add `await` to `create_or_update_device()`

8. **test_get_user_devices** - Line 331
   - Convert to async
   - Add `await` to `get_user_devices()`

9. **test_unlink_device** - Line 347
   - Convert to async
   - Add `await` to `unlink_device()`

10. **test_unlink_last_device_deletes_data** - Line 370
    - Convert to async
    - Add `await` to service calls
    - Convert query to async pattern

11. **test_unlink_device_wrong_user** - Line 405
    - Convert to async
    - Use `create_test_user()` helper

12. **test_cleanup_expired_codes** - Line 424
    - Convert to async
    - Add `await` to `cleanup_expired_codes()`
    - Convert query to async select

13. **test_revoke_user_codes** - Line 448
    - Convert to async
    - Add `await` to `revoke_user_codes()`

### Pattern for Conversion

```python
# BEFORE (sync)
def test_something(db, test_user):
    service = SomeService()
    result = service.some_method(db, test_user.id)
    item = db.query(Model).filter(Model.id == id).first()

# AFTER (async)
@pytest.mark.asyncio
async def test_something(async_db, async_test_user):
    from sqlalchemy import select

    service = SomeService()
    result = await service.some_method(async_db, async_test_user.id)
    result_obj = await async_db.execute(select(Model).where(Model.id == id))
    item = result_obj.scalar_one_or_none()
```

## Migration Script Approach

To complete efficiently, create a script that:
1. Identifies all `def test_*` functions that call now-async service methods
2. Adds `@pytest.mark.asyncio` decorator
3. Changes `def` to `async def`
4. Replaces `db` with `async_db`, `test_user` with `async_test_user`
5. Adds `await` before service method calls
6. Converts `.query()` patterns to `select()` with `await db.execute()`

## Expected Timeline

- **Script creation**: 30 minutes
- **Test execution & debugging**: 1 hour
- **Total**: ~1.5 hours to complete migration

## Benefits After Completion

✅ Fully non-blocking database operations
✅ Better concurrency under load
✅ Consistent async/await patterns throughout
✅ No more hybrid sync/async confusion
✅ Future-proof architecture

## Current Test Status

Before completing remaining conversions:
- ~137/154 tests passing (89%)
- Failures are all due to sync tests calling async methods

After completion:
- Expected: 146-150/154 tests passing (95%+)
- Remaining failures will be genuine bugs (likely streaming transaction issues)
