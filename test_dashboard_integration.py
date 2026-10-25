"""
Smoke test for dashboard integration.
"""

print("Testing Bandhan dashboard integration...\n")

try:
    from dashboard_enhanced import initialize_detector, load_data

    print("✅ Dashboard imports successful")
except Exception as exc:
    print(f"❌ Import error: {exc}")
    raise

borrowers, transactions, regional = load_data()
print(f"✅ Data loaded: {len(borrowers):,} borrowers, {len(transactions):,} transactions")

detector = initialize_detector(borrowers, transactions, regional)
print("✅ Detector initialized")

stats = detector.portfolio_summary()
print(f"✅ Portfolio summary available: {stats}")

clusters = detector.detect_stress_clusters()
flagged = detector.get_flagged_accounts(threshold=45)
print(f"✅ Stress clusters detected: {len(clusters)}")
print(f"✅ High-risk borrowers detected: {len(flagged)}")

print("\n🎉 Dashboard integration looks healthy.")
