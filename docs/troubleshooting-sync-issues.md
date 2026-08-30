# Troubleshooting Board & Card Sync Issues

If cards, comments, or status columns are not updating in real time across team members, follow these steps:

## Step 1: Force Reconnect WebSocket
FlowBoard uses secure WebSockets (wss://sync.flowboard.app) for real-time collaboration.
- **Chrome / Edge / Firefox**: Press \Ctrl + Shift + R\ (Windows/Linux) or \Cmd + Shift + R\ (macOS) to perform a hard refresh and reload cache.
- Look at the top right of the board banner. A green dot indicates **Connected**, while an orange dot indicates **Reconnecting**.

## Step 2: Check Corporate Firewall & Proxy
If your corporate network blocks WebSockets or SSL inspection breaks the handshake:
- Ensure outgoing TCP traffic on port ģ\ to \*.flowboard.app\ and \sync.flowboard.app\ is whitelisted.

## Step 3: Browser Extension Conflicts
Ad-blockers or privacy extensions (e.g., Privacy Badger, uBlock) may block sync scripts. Try disabling extensions on FlowBoard or opening the board in an Incognito/Private window.

## Step 4: Clear Local IndexedDB Cache
1. Open Browser DevTools (\F12\).
2. Go to **Application > Storage > IndexedDB**.
3. Right-click \lowboard_local_cache\ and select **Delete database**.
4. Refresh the page.
