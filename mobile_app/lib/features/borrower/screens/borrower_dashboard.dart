import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../auth/providers/auth_provider.dart';
import '../../../core/utils/glassmorphism_container.dart';

class BorrowerDashboard extends ConsumerWidget {
  const BorrowerDashboard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Borrower Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Health Score Overview
              GlassmorphismContainer(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Text('Loan Health Score', style: TextStyle(color: Colors.grey, fontSize: 16)),
                    const SizedBox(height: 16),
                    Stack(
                      alignment: Alignment.center,
                      children: [
                        SizedBox(
                          width: 150,
                          height: 150,
                          child: CircularProgressIndicator(
                            value: 0.85,
                            strokeWidth: 12,
                            backgroundColor: Colors.white.withValues(alpha: 0.1),
                            color: Colors.green,
                          ),
                        ),
                        Column(
                          children: [
                            Text(
                              '85',
                              style: Theme.of(context).textTheme.displayLarge?.copyWith(
                                color: Colors.green,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const Text('Excellent', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ],
                    ).animate().scale(duration: 600.ms, curve: Curves.easeOutBack),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildStat('Outstanding', '₹ 1,20,000'),
                        _buildStat('Next EMI', '₹ 15,000\n(12 Aug)'),
                        _buildStat('Risk Band', 'Low'),
                      ],
                    ),
                  ],
                ),
              ).animate().fadeIn(),
              
              const SizedBox(height: 24),
              
              // Actions Grid
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                childAspectRatio: 1.1,
                children: [
                  _ActionCard(title: 'Pay EMI', icon: Icons.payment, color: Colors.blue),
                  _ActionCard(title: 'AI Insights', icon: Icons.lightbulb_outline, color: Colors.orange),
                  _ActionCard(title: 'Recovery Center', icon: Icons.health_and_safety, color: Colors.teal),
                  _ActionCard(title: 'Statement', icon: Icons.receipt_long, color: Colors.purple),
                ],
              ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.2, end: 0),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStat(String label, String value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16), textAlign: TextAlign.center),
      ],
    );
  }
}

class _ActionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;

  const _ActionCard({required this.title, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return GlassmorphismContainer(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 32),
          ),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
