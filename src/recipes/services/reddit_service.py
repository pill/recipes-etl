# filkus-recipe-etl
import asyncpraw
from asyncpraw.models import MoreComments


import os
import importlib.metadata
import pathlib
import tomllib # Available in Python 3.11+
from dotenv import load_dotenv
import pprint
import traceback

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
REDDIT_USER_AGENT = f"python:{REDDIT_APP_NAME}:{__version__} (by u/{REDDIT_USERNAME})"

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
    reddit = reddit_service.reddit

    me = await reddit.user.me()
    print(f"✅ Logged in as: {me}")

    try:
        subreddit = await reddit.subreddit("recipes")
        print(f"\n📋 Fetching recent posts from r/recipes...\n")
        
        # Use async for to iterate over the async generator
        async for submission in subreddit.new(limit=1):

            print('--------------------------------')

            # print(post.id, post.created_utc)
            #pprint.pprint(vars(submission))
            await submission.load()

            if submission.is_self: # Check if it's a self-post (text post)
                print(f"Content (Selftext): {submission.selftext[:200]}...") # Truncate for brevity
            else: # It's a link post
                print(f"URL: {submission.url}")


            # Replace 'MoreComments' instances with actual comments
            #await submission.comments.replace_more(limit=None)
            op_name = submission.author.name if submission.author else None
            print(f"Submission ID: {submission.id}")
            # sometimes the recipe a comment from the OP
            print(f"OP Name: {op_name}")

            all_comments = await submission.comments.list()
            
            op_comments_found = False
            recipe_text = None

            for comment in all_comments:
                if isinstance(comment, MoreComments):
                    # In case some 'MoreComments' are missed, skip them
                    continue

                # Check if the comment's author is the OP
                if comment.author and comment.author.name == op_name:
                    print(f"Comment ID: {comment.id}")

                    body_lower = comment.body.lower()
                    if "instructions" in body_lower \
                        or "ingredients" in body_lower \
                        or "preparation" in body_lower \
                        or "prep time" in body_lower \
                        or "cook time" in body_lower \
                        or "total time" in body_lower \
                        or "servings" in body_lower:

                        recipe_text = comment.body
                        # print(f"Comment ID: {comment.id}")
                        break
                    op_comments_found = True

            if recipe_text:
                print(f"Recipe Text: {recipe_text}")
            else:
                print("No recipe text found")
            
            # print(f"Title: {submission.title}")
            # print(f"Score: {submission.score}")
            # print(f"Comments: {submission.num_comments}")
            # print(f"URL: {submission.url}")
            # print(f"Author: {submission.author}")
            # print(f"Created: {submission.created_utc}")
            print(f"--------------------------------")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        
    finally:
        await reddit.close()

async def get_reddit_user():
    """Get the authenticated Reddit user."""
    reddit_service = RedditService()
    try:
        me = await reddit_service.reddit.user.me()
        return me
    finally:
        # Always clean up the connection
        await reddit_service.reddit.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



    