import argparse
import sys
from dotenv import load_dotenv

from src.git_utils import get_git_diff
from src.reviewer import GeminiReviewer, OpenAIReviewer, AnthropicReviewer
from src.github_client import GitHubClient

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Doctor Code: The AI Code Reviewer")
    parser.add_argument("--local", action="store_true", help="Run locally")
    parser.add_argument("--ci", action="store_true", help="Run in GitHub Actions CI mode")
    parser.add_argument("--target", type=str, default="HEAD~1", help="Target commit for local diff")

    parser.add_argument(
        "--provider", 
        type=str, 
        default="gemini", 
        choices=["gemini", "openai", "anthropic"], 
        help="Select the AI provider to use for the code review"
    )
    
    args = parser.parse_args()
    
    try:
        if args.provider == "gemini":
            reviewer = GeminiReviewer()
        elif args.provider == "openai":
            reviewer = OpenAIReviewer()
        elif args.provider == "anthropic":
            reviewer = AnthropicReviewer()
        
        if args.local:
            print(f"🔍 Fetching local git diff against '{args.target}'...")
            diff_text = get_git_diff(target=args.target)
            if not diff_text:
                sys.exit(0)
                
            print("🧠 Analyzing code with Gemini...")
            result = reviewer.review_code(diff_text)
            
            # Print to terminal
            print("\n📋 DOCTOR CODE: REVIEW FINDINGS")
            if not result.findings:
                print("✅ No critical issues found!")
            else:
                for finding in result.findings:
                    print(f"\n- [{finding.category}] {finding.filename} (L{finding.line_number}): {finding.bug_description}")
                    
        elif args.ci:
            print("☁️ Running in CI mode...")
            github = GitHubClient()
            diff_text = github.get_pr_diff()
            
            print("🧠 Analyzing PR diff with Gemini...")
            result = reviewer.review_code(diff_text)
            
            print("📝 Posting results to GitHub PR...")
            github.post_review_comment(result.findings)
            
        else:
            print("Please specify either --local or --ci flag.")
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()