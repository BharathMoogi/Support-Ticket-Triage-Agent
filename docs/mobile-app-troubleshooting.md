# Mobile App Troubleshooting (iOS & Android)

FlowBoard is available for iOS (App Store) and Android (Google Play Store).

## Common Issues & Fixes
- **Biometric Login (FaceID / Fingerprint) Failing**: Go to app **Settings > Security**, toggle Biometric Unlock off and on, and re-authenticate with your master password.
- **Offline Sync Pending**: Cards created while offline are queued in local SQLite storage. When reconnecting to WiFi/Cellular, pull down on the board view to force a synchronization.
- **Clearing Mobile App Cache**:
  - **iOS**: FlowBoard Settings > Storage > Clear Offline Cache.
  - **Android**: Device Settings > Apps > FlowBoard > Storage > Clear Cache.
