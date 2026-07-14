import argparse
import sys
from dotenv import load_dotenv

from src.git_utils import get_git_diff
from src.reviewer import GeminiReviewer, OpenAIReviewer, AnthropicReviewer
from src.github_client import GitHubClient

PROVIDER_NAMES = {"gemini": "Gemini", "openai": "OpenAI", "anthropic": "Anthropic"}
REVIEWERS = {"gemini": GeminiReviewer, "openai": OpenAIReviewer, "anthropic": AnthropicReviewer}

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

    if not args.local and not args.ci:
        print("Please specify either --local or --ci flag.")
        return

    provider_name = PROVIDER_NAMES[args.provider]

    try:
        reviewer = REVIEWERS[args.provider]()

        if args.local:
            print(f"🔍 Fetching local git diff against '{args.target}'...")
            diff_text = get_git_diff(target=args.target)
            if not diff_text:
                sys.exit(0)
                
            print(f"🧠 Analyzing code with {provider_name}...")
            result = reviewer.review_code(diff_text)
            
            # Print to terminal
            print("\n📋 DOCTOR CODE: REVIEW FINDINGS")
            print("=" * 60)
            print(f"📖 PR SUMMARY:\n{result.summary}")
            print("=" * 60)
            
            if not result.findings:
                print("\n✅ No critical issues found!")
            else:
                for finding in result.findings:
                    # Notice the updated attribute names to perfectly match your Pydantic schema
                    print(f"\n- [{finding.category}] {finding.file} (L{finding.line}): {finding.description}")
                    print(f"  💡 Suggestion: {finding.suggestion}")
                    
        elif args.ci:
            print("☁️ Running in CI mode...")
            github = GitHubClient()
            diff_text = github.get_pr_diff()
            
            print(f"🧠 Analyzing PR diff with {provider_name}...")
            result = reviewer.review_code(diff_text)
            
            print("📝 Posting results to GitHub PR...")
            github.post_review_comment(result.summary, result.findings)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()