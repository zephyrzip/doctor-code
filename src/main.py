import argparse
import sys
from dotenv import load_dotenv

# Import our custom modules from Sprint 1 and Sprint 2
from src.git_utils import get_git_diff
from src.reviewer import GeminiReviewer

def main():
    # Securely load the GEMINI_API_KEY from the .env file
    load_dotenv()
    
    # Set up the CLI arguments
    parser = argparse.ArgumentParser(description="Doctor Code: The AI Code Reviewer")
    parser.add_argument(
        "--local", 
        action="store_true", 
        help="Run locally and print the review summary to the terminal"
    )
    parser.add_argument(
        "--target", 
        type=str, 
        default="HEAD~1", 
        help="The git reference to diff against (e.g., HEAD~1, main)"
    )
    
    args = parser.parse_args()
    
    if args.local:
        print(f"🔍 Fetching git diff against '{args.target}'...")
        diff_text = get_git_diff(target=args.target)
        
        if not diff_text:
            print("Notice: No code changes found or failed to get diff. Exiting.")
            sys.exit(0)
            
        print("🧠 Analyzing code with Gemini Flash...")
        try:
            # Initialize our provider and run the review
            reviewer = GeminiReviewer()
            review_result = reviewer.review_code(diff_text)
            
            # Format and print the output to the terminal
            print("\n" + "="*50)
            print("📋 DOCTOR CODE: REVIEW FINDINGS")
            print("="*50)
            
            if not review_result.findings:
                print("✅ No critical issues found! Your code looks clean.")
            else:
                for i, finding in enumerate(review_result.findings, 1):
                    print(f"\n{i}. [{finding.category}] {finding.filename} (Line {finding.line_number})")
                    print(f"   🚨 Issue: {finding.bug_description}")
                    print(f"   💡 Fix:   {finding.suggested_fix}")
            print("\n" + "="*50)
            
        except Exception as e:
            print(f"\n❌ Error during code review execution: {e}", file=sys.stderr)
            
    else:
        # Placeholder for Sprint 4 (CI/CD Pipeline)
        print("CI mode is not yet implemented. Please run with the --local flag for now.")

if __name__ == "__main__":
    main()