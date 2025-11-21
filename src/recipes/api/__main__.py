"""Entry point for running the search API server."""

import sys
import uvicorn

if __name__ == "__main__":
    # Allow port to be specified via command line argument
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    # Use import string for reload to work properly
    uvicorn.run(
        "recipes.api.search_api:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

