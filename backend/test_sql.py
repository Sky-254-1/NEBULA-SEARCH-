#!/usr/bin/env python
"""Test SQLite syntax."""
import sqlite3

conn = sqlite3.connect(':memory:')

# Test 1: CURRENT_TIMESTAMP without parentheses
try:
    conn.execute('CREATE TABLE test1 (id INTEGER PRIMARY KEY, created TEXT DEFAULT CURRENT_TIMESTAMP)')
    conn.execute('INSERT INTO test1 DEFAULT VALUES')
    print("Test 1 passed: CURRENT_TIMESTAMP works without parentheses")
except Exception as e:
    print(f"Test 1 failed: {e}")

# Test 2: CURRENT_TIMESTAMP with parentheses  
try:
    conn.execute('CREATE TABLE test2 (id INTEGER PRIMARY KEY, created TEXT DEFAULT (CURRENT_TIMESTAMP))')
    conn.execute('INSERT INTO test2 DEFAULT VALUES')
    print("Test 2 passed: CURRENT_TIMESTAMP works with parentheses")
except Exception as e:
    print(f"Test 2 failed: {e}")

# Test 3: datetime('now') without parentheses
try:
    conn.execute('CREATE TABLE test3 (id INTEGER PRIMARY KEY, created TEXT DEFAULT datetime(''now''))')
    conn.execute('INSERT INTO test3 DEFAULT VALUES')
    print("Test 3 passed: datetime('now') works without parentheses")
except Exception as e:
    print(f"Test 3 failed: {e}")

conn.close()
