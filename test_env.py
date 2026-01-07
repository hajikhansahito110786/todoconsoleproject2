import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 60)
print("DEBUGGING DATABASE_URL ISSUE")
print("=" * 60)
print(f"Type of DATABASE_URL: {type(DATABASE_URL)}")
print(f"Length of DATABASE_URL: {len(DATABASE_URL)}")
print(f"Raw DATABASE_URL value: '{DATABASE_URL}'")
print(f"First 10 chars: '{DATABASE_URL[:10]}'")
print(f"Last 10 chars: '{DATABASE_URL[-10:]}'")
print("=" * 60)

# Check for quotes
if DATABASE_URL:
    if DATABASE_URL[0] == "'" and DATABASE_URL[-1] == "'":
        print("⚠️  Found single quotes at start and end!")
        print(f"Before stripping: '{DATABASE_URL}'")
        DATABASE_URL = DATABASE_URL.strip("'")
        print(f"After stripping: '{DATABASE_URL}'")
    elif DATABASE_URL[0] == '"' and DATABASE_URL[-1] == '"':
        print('⚠️  Found double quotes at start and end!')
        print(f'Before stripping: "{DATABASE_URL}"')
        DATABASE_URL = DATABASE_URL.strip('"')
        print(f'After stripping: "{DATABASE_URL}"')
    else:
        print("✅ No quotes found at start/end")
else:
    print("❌ DATABASE_URL is None or empty!")