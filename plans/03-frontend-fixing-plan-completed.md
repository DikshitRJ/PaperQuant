## Goal Description
Implement "Phase 3: Frontend Fixing & Wiring" to replace the outdated `pywebview` communication layer with a modern standard HTTP/WebSocket interface. This aligns the frontend with the `docs/api-spec.md` contract.
We will address critical data mismatches (e.g., `PositionsTable`, `ExecutionTerminal`), wire up "dead" UI components (`HomeView`, `SetupView`, `AlgorithmsView`), and establish a robust shared TypeScript type system.

## User Review Required
> [!IMPORTANT] 
> This change fundamentally alters how the React frontend talks to the backend. It removes the legacy `window.pywebview` globals. Ensure that the Python backend (Phase 2) is running an HTTP/WebSocket server before testing this frontend integration.

## Open Questions
> [!WARNING]
> We will be dropping `useBackend.ts` completely and relying on the new `useApi.ts` and `useWebSocket.ts`. 
> Does the API port discovery logic (reading `window.__PAPERQUANT_PORT__` or `VITE_API_PORT`) look sufficient for the upcoming Tauri packaging?

## Proposed Changes

### Types & API Client (Foundation)
Define the core HTTP client and shared type contracts based on `docs/api-spec.md`.
#### [NEW] src/types/api.ts
All TypeScript interfaces (`Position`, `LogEntry`, `Settings`, `WSEvent`, etc.)
#### [NEW] src/lib/api-client.ts
The core API client wrapper for `fetch` requests with port discovery.
#### [NEW] src/hooks/useWebSocket.ts
React hook to manage WebSocket connection (`ws://.../ws`), reconnection logic, and event dispatch.
#### [DELETE] src/hooks/useBackend.ts
Legacy pywebview logic.

---
### Context & State Management
#### [MODIFY] src/context/PaperQuantContext.tsx
Remove all `window.*` assignments. Import types from `src/types/api.ts`. Use `useWebSocket` to listen for server events (`positions_update`, `log`, `stats_update`) and update React state appropriately.

---
### UI Components (Wiring & Fixes)
#### [MODIFY] src/App.tsx
Replace `useBackend` with `apiClient`. Handle session start/stop/reset via API calls. Pass configuration cleanly to `SetupView`.
#### [MODIFY] src/components/SetupView.tsx
Fetch strategies from API on mount to populate the strategy dropdown. Pass `watchlist` and `strategy_id` to `App.tsx` on start.
#### [MODIFY] src/components/AlgorithmsView.tsx
Implement missing `setAlgos` setter. Wire up "Register", "Delete", and "Configure & Run" buttons to their respective `apiClient` methods.
#### [MODIFY] src/components/SettingsView.tsx
Fetch settings on mount. Wire changes to `PUT /api/settings`. Implement dynamic version/health connection check in the UI.
#### [MODIFY] src/components/PositionsTable.tsx
Use the updated `Position` interface. Fix `TypeError` by correctly safely checking `pos.pnl?.startsWith('+')`.
#### [MODIFY] src/components/ExecutionTerminal.tsx
Wire "Clear Logs" button to `setLogs([])` from context.
#### [MODIFY] src/components/HomeView.tsx
Render real global stats, system pulse, and generate SVG chart from `chartData`.

## Verification Plan

### Automated Tests
```bash
cd UI/Frontend
npx tsc --noEmit
npm run lint
npm run build
```

### Manual Verification
1. Start the API server in another terminal (`python api_server.py`).
2. Run `npm run dev` in `UI/Frontend` with `VITE_API_PORT=8000`.
3. Validate HomeView chart and stats are not "dead".
4. Validate SetupView dropdown populates.
5. Validate session starts and logs appear correctly in ExecutionTerminal.
6. Validate Settings updates are persisted.
