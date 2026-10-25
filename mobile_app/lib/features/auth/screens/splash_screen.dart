import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Placeholder for logo
            Icon(Icons.security, size: 80, color: Theme.of(context).primaryColor)
              .animate()
              .scale(duration: 600.ms, curve: Curves.easeOutBack)
              .fadeIn(duration: 600.ms),
            const SizedBox(height: 24),
            Text(
              'SatarkSetu',
              style: Theme.of(context).textTheme.displayLarge,
            ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.5, end: 0),
            const SizedBox(height: 8),
            Text(
              'Secure. Transparent. Empowering.',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(color: Colors.grey),
            ).animate().fadeIn(delay: 600.ms),
          ],
        ),
      ),
    );
  }
}
