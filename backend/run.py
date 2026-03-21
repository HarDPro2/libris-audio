import traceback
import sys

print("=== STARTING LIBRIS BACKEND ===", flush=True)
try:
    import uvicorn
    print("Uvicorn imported successfully.", flush=True)
    import main
    print("Main module imported successfully.", flush=True)
    
    if __name__ == "__main__":
        print("Starting Uvicorn explicitly...", flush=True)
        uvicorn.run(main.app, host="0.0.0.0", port=10000)
except Exception as e:
    print("!!! FATAL BOOT ERROR !!!", flush=True)
    traceback.print_exc()
    sys.exit(1)
