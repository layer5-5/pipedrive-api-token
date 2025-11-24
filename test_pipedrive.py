#!/usr/bin/env python3

import sys

sys.path.insert(0, "src")

from pipedrive import Pipedrive


def test():
    print("Testing pipedrive import...")
    try:
        p = Pipedrive("test_token")
        print(f"Success! Created: {p}")
        print(f"Type: {type(p)}")
        print(f"Available methods: {[m for m in dir(p) if not m.startswith('_')]}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test()
