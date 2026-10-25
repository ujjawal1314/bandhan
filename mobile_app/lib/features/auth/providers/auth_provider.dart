import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../services/auth_service.dart';
import '../../../core/network/api_client.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final authServiceProvider = Provider<AuthService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthService(apiClient);
});

final secureStorageProvider = Provider<FlutterSecureStorage>((ref) => const FlutterSecureStorage());

enum AuthState { initial, loading, authenticated, error, unauthenticated }

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;
  final FlutterSecureStorage _storage;
  String? _currentRole;

  AuthNotifier(this._authService, this._storage) : super(AuthState.initial) {
    _checkAuthStatus();
  }

  String? get role => _currentRole;

  Future<void> _checkAuthStatus() async {
    final token = await _storage.read(key: 'jwt_token');
    final savedRole = await _storage.read(key: 'user_role');
    
    if (token != null && savedRole != null) {
      _currentRole = savedRole;
      state = AuthState.authenticated;
    } else {
      state = AuthState.unauthenticated;
    }
  }

  Future<void> sendOtp(String phone, String role) async {
    state = AuthState.loading;
    try {
      await _authService.sendOtp(phone, role);
      state = AuthState.initial; // Go back to initial to show OTP input, or use a new state
    } catch (e) {
      state = AuthState.error;
    }
  }

  Future<void> verifyOtp(String phone, String otp, String role) async {
    state = AuthState.loading;
    try {
      final token = await _authService.verifyOtp(phone, otp, role);
      await _storage.write(key: 'jwt_token', value: token);
      await _storage.write(key: 'user_role', value: role);
      _currentRole = role;
      state = AuthState.authenticated;
    } catch (e) {
      state = AuthState.error;
    }
  }

  Future<void> logout() async {
    state = AuthState.loading;
    try {
      await _authService.logout();
    } finally {
      await _storage.delete(key: 'jwt_token');
      await _storage.delete(key: 'user_role');
      _currentRole = null;
      state = AuthState.unauthenticated;
    }
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(
    ref.watch(authServiceProvider),
    ref.watch(secureStorageProvider),
  );
});
