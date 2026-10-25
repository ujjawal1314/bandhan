import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/auth/screens/role_selection_screen.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/otp_verification_screen.dart';
import '../../features/borrower/screens/borrower_dashboard.dart';
import '../../features/field_officer/screens/officer_dashboard.dart';
import '../../features/auth/screens/splash_screen.dart';

final goRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  final authNotifier = ref.read(authProvider.notifier);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: _GoRouterRefreshStream(
      ref.watch(authProvider.notifier).stream, // Not optimal in Riverpod 2+, but sufficient for this architecture setup. In reality we could use GoRouterRefreshStream
    ),
    redirect: (context, state) {
      final isAuth = authState == AuthState.authenticated;
      final isLoggingIn = state.matchedLocation == '/login' || 
                          state.matchedLocation == '/role' || 
                          state.matchedLocation == '/otp';
      
      if (authState == AuthState.initial || authState == AuthState.loading) {
        // Allow access to login pages during loading/initial
        if (state.matchedLocation == '/splash') return null;
      }

      if (!isAuth && !isLoggingIn) {
        return '/role';
      }

      if (isAuth && isLoggingIn) {
        if (authNotifier.role == 'borrower') {
          return '/borrower';
        } else if (authNotifier.role == 'officer') {
          return '/officer';
        }
      }

      // Root redirect for authenticated users
      if (isAuth && state.matchedLocation == '/') {
        if (authNotifier.role == 'borrower') return '/borrower';
        if (authNotifier.role == 'officer') return '/officer';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/role',
        builder: (context, state) => const RoleSelectionScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) {
          final role = state.uri.queryParameters['role'] ?? 'borrower';
          return LoginScreen(role: role);
        },
      ),
      GoRoute(
        path: '/otp',
        builder: (context, state) {
          final phone = state.uri.queryParameters['phone'] ?? '';
          final role = state.uri.queryParameters['role'] ?? 'borrower';
          return OtpVerificationScreen(phone: phone, role: role);
        },
      ),
      GoRoute(
        path: '/borrower',
        builder: (context, state) => const BorrowerDashboard(),
      ),
      GoRoute(
        path: '/officer',
        builder: (context, state) => const OfficerDashboard(),
      ),
    ],
  );
});

// Helper for Riverpod + GoRouter redirect updates
class _GoRouterRefreshStream extends ChangeNotifier {
  _GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen(
      (dynamic _) => notifyListeners(),
    );
  }
  late final dynamic _subscription;
  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
