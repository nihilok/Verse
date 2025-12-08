# Frontend Dependency Upgrade Plan

**Status:** Planned
**Created:** 2025-12-08
**Priority:** Medium
**Estimated Effort:** 4-8 hours

## Overview

This plan outlines the strategy for upgrading major frontend dependencies that were deferred during the recent dependency update (commit `5f99b9a`). These updates involve major version changes that may introduce breaking changes and require careful testing.

## Current Status

✅ **Already Updated (2025-12-08):**
- React: 19.2.0 → 19.2.1
- React DOM: 19.2.0 → 19.2.1
- TypeScript tooling: 8.46.2 → 8.48.1
- Prettier: 3.6.2 → 3.7.4
- Tailwind CSS: 4.1.16 → 4.1.17
- All minor/patch updates applied

## Deferred Major Updates

### 1. ESLint 8 → 9

**Current:** `8.57.1`
**Latest:** `9.39.1`
**Breaking Changes:** Yes - major configuration rewrite

#### Migration Steps

1. **Review breaking changes:**
   - ESLint 9 uses a new flat config format
   - Many plugins need updates
   - Some rules renamed or removed

2. **Update configuration:**
   \`\`\`bash
   # Backup current config
   cp .eslintrc.cjs .eslintrc.cjs.backup

   # Use migration tool
   npx @eslint/migrate-config .eslintrc.cjs
   \`\`\`

3. **Update dependencies:**
   \`\`\`bash
   bun update eslint@^9.0.0
   bun update @eslint/js@^9.0.0
   bun update eslint-plugin-react-hooks@^7.0.0
   \`\`\`

4. **Convert to flat config:**
   - Rename `.eslintrc.cjs` to `eslint.config.js`
   - Use new flat config format
   - Update all plugin references

5. **Test thoroughly:**
   \`\`\`bash
   bun run lint
   bun run lint:fix
   \`\`\`

#### Resources
- [ESLint Migration Guide](https://eslint.org/docs/latest/use/migrate-to-9.0.0)
- [Flat Config Guide](https://eslint.org/docs/latest/use/configure/configuration-files)

#### Estimated Time
2-3 hours

---

### 2. Vite 5 → 7

**Current:** `5.4.21`
**Latest:** `7.2.6`
**Breaking Changes:** Yes - major version jump

#### Migration Steps

1. **Review Vite 6 and 7 breaking changes:**
   - Check [Vite 6 Migration Guide](https://vite.dev/guide/migration-from-v5)
   - Check [Vite 7 Migration Guide](https://vite.dev/guide/migration-from-v6)
   - Environment variable handling changes
   - Plugin API changes

2. **Update Vite and plugin:**
   \`\`\`bash
   bun update vite@^7.0.0
   bun update @vitejs/plugin-react@^5.0.0
   \`\`\`

3. **Update configuration:**
   - Review `vite.config.ts`
   - Update plugin configurations
   - Check environment variable usage

4. **Test build and dev server:**
   \`\`\`bash
   bun run dev
   bun run build
   bun run preview
   \`\`\`

5. **Check for plugin compatibility:**
   - `vite-plugin-pwa` - already updated to 1.2.0
   - `@vitejs/plugin-react` - needs update to v5
   - `@tailwindcss/vite` - check compatibility

#### Potential Issues
- Environment variables may need prefix changes
- Build output structure may change
- Dev server behaviour differences

#### Estimated Time
2-3 hours

---

### 3. Vitest 1 → 4

**Current:** `1.6.1`
**Latest:** `4.0.15`
**Breaking Changes:** Yes - major version jump

#### Migration Steps

1. **Review Vitest 2, 3, and 4 breaking changes:**
   - Check [Vitest 2 Migration](https://vitest.dev/guide/migration.html)
   - Check for Vitest 3 and 4 changes
   - API changes for test context and mocking

2. **Update Vitest:**
   \`\`\`bash
   bun update vitest@^4.0.0
   \`\`\`

3. **Update test configuration:**
   - Review `vite.config.ts` test section
   - Check for deprecated options
   - Update test globals if needed

4. **Update test files:**
   - Check for deprecated APIs
   - Update mocking syntax if changed
   - Review assertion APIs

5. **Run all tests:**
   \`\`\`bash
   bun test
   bun run test:unit
   \`\`\`

6. **Fix any failing tests:**
   - Address API changes
   - Update snapshot files if needed
   - Fix type issues

#### Estimated Time
2-3 hours

---

### 4. jsdom 22 → 27

**Current:** `22.1.0`
**Latest:** `27.2.0`
**Breaking Changes:** Likely - major version jump

#### Migration Steps

1. **Check jsdom changelogs:**
   - Review versions 23, 24, 25, 26, 27
   - Look for DOM API changes
   - Check Node.js compatibility

2. **Update jsdom:**
   \`\`\`bash
   bun update jsdom@^27.0.0
   \`\`\`

3. **Run tests:**
   \`\`\`bash
   bun test
   \`\`\`

4. **Fix compatibility issues:**
   - DOM API behaviour changes
   - Event handling differences
   - Form behaviour changes

#### Estimated Time
1-2 hours

---

### 5. globals 15 → 16

**Current:** `15.15.0`
**Latest:** `16.5.0`
**Breaking Changes:** Possible

#### Migration Steps

1. **Update globals:**
   \`\`\`bash
   bun update globals@^16.0.0
   \`\`\`

2. **Check ESLint configuration:**
   - Verify global definitions still work
   - Update if new globals needed

3. **Test linting:**
   \`\`\`bash
   bun run lint
   \`\`\`

#### Estimated Time
0.5-1 hour

---

## Recommended Approach

### Phase 1: Preparation (30 minutes)
1. ✅ Create this upgrade plan
2. ✅ Document current versions
3. Create a new branch: `chore/upgrade-frontend-deps`
4. Commit current working state

### Phase 2: Testing Infrastructure (2-3 hours)
**Order:** jsdom → Vitest → Vite

**Rationale:** Testing tools should be stable before upgrading build tools.

1. Upgrade **jsdom** first (least risk)
2. Upgrade **Vitest** second (depends on stable jsdom)
3. Upgrade **Vite** third (depends on stable test environment)

### Phase 3: Linting Tools (2-3 hours)
**Order:** globals → ESLint

1. Upgrade **globals** (minor impact)
2. Upgrade **ESLint** last (most complex)

### Phase 4: Verification (1 hour)
1. Run full test suite
2. Test dev server
3. Test production build
4. Manual smoke testing
5. Check bundle sizes

### Phase 5: Documentation & Cleanup (30 minutes)
1. Update this plan with "Completed" status
2. Document any issues encountered
3. Update CHANGELOG.md
4. Create PR for review

## Testing Checklist

After each upgrade, verify:

- [ ] `bun run dev` - Dev server starts
- [ ] `bun run build` - Build succeeds
- [ ] `bun run lint` - No linting errors
- [ ] `bun test` - All tests pass
- [ ] `bun run preview` - Preview works
- [ ] Manual smoke test in browser
- [ ] No console errors/warnings
- [ ] PWA still works
- [ ] Dark mode still works
- [ ] All components render correctly

## Rollback Plan

If major issues are encountered:

1. **Revert individual package:**
   \`\`\`bash
   bun update package-name@old-version
   \`\`\`

2. **Revert all changes:**
   \`\`\`bash
   git checkout main -- frontend/package.json frontend/bun.lock
   bun install
   \`\`\`

3. **Document issues:**
   - Create issue in repository
   - Note which version caused problems
   - Document any workarounds attempted

## Risk Assessment

| Dependency | Risk Level | Reason |
|------------|-----------|--------|
| ESLint 8→9 | 🟡 Medium | Major config changes, but well documented |
| Vite 5→7 | 🟡 Medium | Two major versions, possible breaking changes |
| Vitest 1→4 | 🟡 Medium | Three major versions, API changes likely |
| jsdom 22→27 | 🟠 Low-Medium | Five major versions, but isolated to tests |
| globals 15→16 | 🟢 Low | Minor impact, mostly type definitions |

## Success Criteria

- ✅ All tests pass
- ✅ No new linting errors
- ✅ Build completes successfully
- ✅ Dev server runs without errors
- ✅ Application functions correctly in browser
- ✅ No regression in functionality
- ✅ Bundle size does not increase significantly (>5%)
- ✅ Build time does not increase significantly (>20%)

## Notes

- Consider doing this upgrade on a low-traffic day
- Have a team member available for code review
- Consider running in staging environment first
- Document any new warnings or deprecations for future reference

## Related Issues

- None yet

## Progress Tracking

- [ ] Phase 1: Preparation
- [ ] Phase 2: Testing Infrastructure
  - [ ] jsdom upgrade
  - [ ] Vitest upgrade
  - [ ] Vite upgrade
- [ ] Phase 3: Linting Tools
  - [ ] globals upgrade
  - [ ] ESLint upgrade
- [ ] Phase 4: Verification
- [ ] Phase 5: Documentation

## Completion

**Date Completed:** _Not yet started_
**Final Commit:** _TBD_
**Issues Encountered:** _TBD_
**Lessons Learned:** _TBD_
