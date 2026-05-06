import os
import sys
import subprocess

def run_evals():
    print("\n========================================================")
    print("🚀 Running System Evaluation Suite (run_evals.py)...")
    print("========================================================\n")
    try:
        # Run run_evals.py
        result = subprocess.run([sys.executable, "run_evals.py"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to execute run_evals.py: {e}")
        return False

def verify_safety():
    evals_path = "EVALS.md"
    if not os.path.exists(evals_path):
        print(f"❌ Error: {evals_path} does not exist. Run run_evals.py first.")
        return False
        
    with open(evals_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check for safety section specifically
    safety_section = ""
    if "## 2. Safety Tests" in content:
        safety_section = content.split("## 2. Safety Tests")[1]
        if "## 3." in safety_section:
            safety_section = safety_section.split("## 3.")[0]
            
    # Check if 'FAIL' exists in the safety section
    has_safety_fail = "FAIL" in safety_section if safety_section else False
    has_global_fail = "FAIL" in content
    
    if has_safety_fail:
        print("\n" + "!" * 60)
        print("🚨 CRITICAL ALERT: SAFETY GUARDRAIL FAILURE DETECTED!")
        print("Your recent changes broke one or more safety tests in EVALS.md.")
        print("Pre-push validation failed. Aborting to protect production.")
        print("!" * 60 + "\n")
        return False
    elif has_global_fail:
        print("\n⚠️ WARNING: Some non-safety checks failed in EVALS.md.")
        print("Please review the full report before deploying to production.\n")
        return True
    else:
        print("\n========================================================")
        print("✅ ALL SYSTEMS GREEN: Safety and Retrieval Evals Passed!")
        print("Ready for safe deployment.")
        print("========================================================\n")
        return True

if __name__ == "__main__":
    # Ensure working directory is the repository root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)
    
    if not run_evals():
        print("❌ Evaluation execution failed.")
        sys.exit(1)
        
    if not verify_safety():
        sys.exit(1)
        
    sys.exit(0)
