#!/usr/bin/env python3
"""
Pre-build verification script to ensure AI dependencies are not being installed.
This script will FAIL LOUDLY if it detects torch, groq, or other AI packages.
"""
import sys
import subprocess

FORBIDDEN_PACKAGES = [
    'torch',
    'groq',
    'together',
    'tiktoken',
    'sentence-transformers',
    'transformers',
]

print("=" * 80)
print("VERIFYING NO AI DEPENDENCIES ARE INSTALLED")
print("=" * 80)

# Check installed packages
result = subprocess.run(
    ['pip', 'list', '--format=freeze'],
    capture_output=True,
    text=True
)

installed = result.stdout.lower()

found_forbidden = []
for pkg in FORBIDDEN_PACKAGES:
    if pkg.lower() in installed:
        found_forbidden.append(pkg)

if found_forbidden:
    print("\n🚨 ERROR: FORBIDDEN AI DEPENDENCIES DETECTED! 🚨")
    print(f"Found: {', '.join(found_forbidden)}")
    print("\nThese packages should NOT be installed in production.")
    print("This indicates stale cached dependencies or incorrect configuration.")
    print("\n" + "=" * 80)
    sys.exit(1)

print("✅ No forbidden AI dependencies detected")
print("=" * 80)
sys.exit(0)
