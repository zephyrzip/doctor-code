import subprocess
import sys

def get_git_diff(target: str = "HEAD~1") -> str:
    """
    Executes a native git command to extract the diff of modified code.
    
    Args:
        target (str): The git reference to diff against (e.g., 'HEAD~1', 'main', or unstaged if empty).
        
    Returns:
        str: A clean, UTF-8 decoded string of the git diff.
    """
    try:
        cmd = ["git", "diff", target]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",  # 🚨 THE FIX: Force UTF-8 decoding for Windows compatibility
            errors="replace",  # Safety net: replaces completely broken characters instead of crashing
            check=True
        )
        
        # Secondary safety net: ensure stdout isn't None before stripping
        if result.stdout is None:
            return ""
            
        diff_text = result.stdout.strip()
        
        if not diff_text:
            print(f"Notice: No changes found against {target}.")
            
        return diff_text

    except subprocess.CalledProcessError as e:
        # e.stderr might also be None depending on how the process failed
        err_msg = e.stderr if e.stderr else "Unknown error"
        print(f"CRITICAL: Git command failed. {err_msg}", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("CRITICAL: Git is not installed or not found in your system PATH.", file=sys.stderr)
        return ""