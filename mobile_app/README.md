# SatarkSetu Mobile Application

This is the official companion Flutter application for SatarkSetu, containing two distinct applications unified under a single binary:
1. **Borrower App**: For end borrowers to view their loan health, pay EMIs, and access recovery support.
2. **Field Officer App**: For agents to manage visits, optimize routes, and record recovery notes.

## Architecture

The application is built using **Clean Architecture** combined with **Riverpod** for state management and **GoRouter** for navigation.

### Folder Structure
```
lib/
├── core/                   # App-wide configurations
│   ├── network/            # Dio API Client and Interceptors
│   ├── router/             # GoRouter setup for role-based navigation
│   ├── theme/              # Glassmorphism design system & Google Fonts
│   └── utils/              # Reusable UI components (GlassmorphismContainer)
├── features/               # Feature-based modular structure
│   ├── auth/               # Login, OTP Verification, Role Selection
│   ├── borrower/           # Dashboard, Payments, Health UI
│   └── field_officer/      # Route optimization, Visit Logs, Offline Mode
└── main.dart               # Entry point
```

## API Configuration Guide

The app relies on `ApiClient` (`lib/core/network/api_client.dart`) to communicate with the existing Python backend.

### Environment Setup
Create a `.env` file in the root of this project (use `.env.example` as a template):
```env
BASE_URL=http://localhost:8000
ENVIRONMENT=development
```

### Extending Authentication
Currently, `AuthService` (`lib/features/auth/services/auth_service.dart`) uses mocked delays to simulate OTP sending and verification without modifying your existing backend.
To connect your real backend later, implement these endpoints in your Python server and uncomment the API calls in `AuthService`:
- `POST /auth/send-otp` : `{ "phone": "1234567890", "role": "borrower" }`
- `POST /auth/verify-otp`: `{ "phone": "1234567890", "otp": "1234", "role": "borrower" }` -> Returns `{ "token": "JWT_TOKEN" }`

The `ApiClient` will automatically attach the saved `JWT_TOKEN` to all subsequent API calls as a `Bearer` token.

## Build Instructions

### Prerequisites
- [Flutter SDK](https://docs.flutter.dev/get-started/install) (v3.0+)
- Android Studio (for Android builds)
- Xcode (for iOS builds, macOS only)

### Setup
1. Run `flutter clean`
2. Run `flutter pub get`

### Running Locally
To run the app on an attached device or emulator:
```bash
flutter run
```

### Android Build Instructions
To build a production APK:
```bash
flutter build apk --release
```
The APK will be generated at `build/app/outputs/flutter-apk/app-release.apk`.

To build an App Bundle for the Google Play Store:
```bash
flutter build appbundle --release
```

### iOS Build Instructions (macOS only)
To build a production IPA:
1. Ensure your Apple Developer account is configured in Xcode.
2. Run:
```bash
flutter build ipa --release
```
The generated archive can be uploaded to App Store Connect via the Transporter app.

## Security
- JWT Tokens and user roles are stored securely using `flutter_secure_storage` which utilizes Android Keystore and iOS Keychain.
- No secrets are hardcoded in the application.
