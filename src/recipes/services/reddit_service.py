# filkus-recipe-etl
import asyncpraw
import os
import importlib.metadata
import pathlib
import tomllib # Available in Python 3.11+
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get version from pyproject.toml
__version__ = "1.2.0"  # Default fallback
try:
    toml_path = pathlib.Path(__file__).resolve().parents[3] / "pyproject.toml"
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
            __version__ = data.get('tool', {}).get('poetry', {}).get('version', __version__)
except Exception:
    # If reading from file fails, try installed package metadata
    try:
        __version__ = importlib.metadata.version("recipes-etl")
    except Exception:
        pass  # Keep default version

REDDIT_APP_NAME = os.getenv('REDDIT_APP_NAME')
REDDIT_CLIENT_ID=os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET=os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')

# ' python:filkus-recipe-etl:1.2.0 (by u/filku)"
REDDIT_USER_AGENT = f"python:{os.getenv('REDDIT_USER_AGENT')}:{__version__} (by u/{REDDIT_USERNAME})"

class RedditService:
    def __init__(self):
        self.reddit = asyncpraw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            password=REDDIT_PASSWORD,
            user_agent=REDDIT_USER_AGENT,
            username=REDDIT_USERNAME,
        )

async def main():
    """Test Reddit service."""
    reddit_service = RedditService()
    me = await reddit_service.reddit.user.me()
    print(f"✅ Logged in as: {me}")
    await reddit_service.reddit.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



    