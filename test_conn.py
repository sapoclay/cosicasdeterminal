#!/usr/bin/env python3
"""Test simple para connection_manager"""

try:
    from connection_manager import ConnectionApp
    print("Import exitoso")
    app = ConnectionApp()
    print("App creada")
    app.run()
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    with open("conn_test_error.log", "w") as f:
        f.write(traceback.format_exc())
