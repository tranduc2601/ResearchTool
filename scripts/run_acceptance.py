"""Automated Acceptance Test Harness."""
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run the final acceptance test.")
    parser.add_argument("--platform", type=str, default="windows", choices=["windows", "android"])
    parser.add_argument("--model", type=str, default="qwen2-vl")
    args = parser.parse_args()

    print("==================================================")
    print("      RESEARCH TOOL - FINAL ACCEPTANCE TEST       ")
    print("==================================================")
    print(f"Goal     : Find ergonomic chairs around 2M")
    print(f"Platform : {args.platform.upper()}")
    print(f"Model    : {args.model}")
    print("==================================================\n")
    
    print("[WARNING] This will execute REAL clicks and typing on your machine.")
    print("[WARNING] Do not move your mouse during execution.")
    response = input("Proceed? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
        
    cmd = [
        ".venv\\Scripts\\python.exe",
        "-m", "research_tool.cli.main",
        "Find ergonomic chairs around 2M",
        "--platform", args.platform,
        "--model", args.model
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Test failed with exit code {e.returncode}")
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
        
if __name__ == "__main__":
    main()
