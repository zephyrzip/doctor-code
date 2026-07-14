import os

def process_user_data(user_input):
    # Bug 1: Hardcoded sensitive API key (Security flaw)
    SECRET_API_KEY = "sk_live_51NzABC123FakeKeyDoNotUse"
    
    # Bug 2: Classic SQL Injection vulnerability (Security flaw)
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    print(f"Executing raw query: {query}")
    
    # Bug 3: Infinite loop risk if index isn't handled (Logic bug)
    i = 0
    while i < 10:
        print("Processing...")
        # Missing i += 1 statement!
        
    return True