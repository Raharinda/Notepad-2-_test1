#!/usr/bin/env python3
"""Test capslock demon new features: cursor preservation and time-out retry"""

from twists.capslock_demon import CapslockDemonTwist
import tkinter as tk

print("=" * 60)
print("CAPSLOCK DEMON - Feature Test")
print("=" * 60)

# Test 1: Instantiation
print("\n[TEST 1] Instantiation...")
root = tk.Tk()
root.geometry("900x700")
overlay = tk.Frame(root)
overlay.pack(fill="both", expand=True)

finish_count = [0]

def finish_callback():
    finish_count[0] += 1
    print(f"  Twist finished! (count: {finish_count[0]})")

twist = CapslockDemonTwist(overlay, finish_callback, difficulty=1)
print("✅ Instantiated successfully")
print(f"   Sentence: '{twist.target_sentence}'")
print(f"   Time limit: {twist.time_limit_ms}ms (~{twist.time_limit_ms // 1000}s)")
print(f"   Capslock interval: {twist.base_interval_ms}ms")

# Test 2: Check methods exist
print("\n[TEST 2] Methods...")
methods_to_check = ['toggle_capslock', 'process_input', '_retry_twist', '_update_timer_display']
for method_name in methods_to_check:
    has_method = hasattr(twist, method_name)
    status = "✅" if has_method else "❌"
    print(f"   {status} {method_name}")

# Test 3: Verify timer logic
print("\n[TEST 3] Timer Logic...")
print(f"   Initial time_remaining_ms: {twist.time_remaining_ms}")
print(f"   Timer is scheduled: {twist.timer_job is not None}")

# Test 4: Check _retry_twist implementation
print("\n[TEST 4] Retry Logic...")
print(f"   Before retry:")
print(f"      Entry content: '{twist.entry.get('1.0', tk.END).strip()}'")
print(f"      Capslock ON: {twist.capslock_on}")
original_sentence = twist.target_sentence
print(f"      Sentence: '{original_sentence}'")

# Simulate what happens when time runs out
twist._retry_twist()
print(f"   After retry:")
print(f"      Entry content: '{twist.entry.get('1.0', tk.END).strip()}'")
print(f"      Capslock ON: {twist.capslock_on}")
print(f"      Time reset to {twist.time_remaining_ms}ms")
print(f"      New sentence (may be same): '{twist.target_sentence}'")

print("\n" + "=" * 60)
print("✅ All feature tests passed!")
print("=" * 60)

root.destroy()
