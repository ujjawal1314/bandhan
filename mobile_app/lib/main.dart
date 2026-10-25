import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'core/router/app_router.dart';

void main() {
  runApp(const ProviderScope(child: SatarkSetuMobile()));
}

class SatarkSetuMobile extends ConsumerWidget {
  const SatarkSetuMobile({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(goRouterProvider);

    return MaterialApp.router(
      title: 'SatarkSetu Mobile',
      theme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark, // Default to dark for branding
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
