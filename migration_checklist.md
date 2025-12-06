# Async DB Migration Checklist

## Core Infrastructure
- [x] Add asyncpg dependency to pyproject.toml
- [x] Update database.py with AsyncEngine and AsyncSession
- [x] Update main.py to use async_engine
- [x] bible_service.py - save_passage

## Services to Migrate

### chat_service.py (4 methods)
- [ ] get_chat_messages - Convert to async with select()
- [ ] clear_chat_messages - Convert to async
- [ ] get_standalone_chats - Convert to async with select()
- [ ] delete_standalone_chat - Convert to async

### definition_service.py (3 methods)
- [ ] link_definition_to_user - Convert to async
- [ ] get_user_definitions - Convert to async with select()
- [ ] clear_user_definitions - Convert to async

### device_link_service.py (6 methods)
- [ ] generate_link_code - Convert to async
- [ ] merge_users - Convert to async
- [ ] get_user_devices - Convert to async with select()
- [ ] unlink_device - Convert to async
- [ ] cleanup_expired_codes - Convert to async
- [ ] revoke_user_codes - Convert to async

### insight_service.py (3 methods)
- [ ] link_insight_to_user - Convert to async
- [ ] get_user_insights - Convert to async with select()
- [ ] clear_user_insights - Convert to async

### user_service.py (6 methods)
- [ ] get_or_create_user - Convert to async with select()
- [ ] get_user_by_anonymous_id - Convert to async with select()
- [ ] _link_insight_to_user - Convert to async
- [ ] clear_user_data - Convert to async
- [ ] export_user_data - Convert to async with select()
- [ ] import_user_data - Convert to async

## Routes to Update (app/api/routes.py)
All 27 route handlers need:
- [ ] Change Session -> AsyncSession in Depends(get_db)
- [ ] Add await to all service method calls
- [ ] Verify all handlers are async def

## Testing
- [ ] Update test fixtures for AsyncSession
- [ ] Run full test suite
- [ ] Manual testing of key workflows

## Documentation
- [ ] Update ASYNC_DB_MIGRATION.md with final status
- [ ] Update README if needed
