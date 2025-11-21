# Switching to Python 3.12

This guide helps you switch from Python 3.13 to Python 3.12 to enable embeddings support.

## Step 1: Install Python 3.12

### Option A: Using Homebrew (Recommended)

```bash
# Install Python 3.12
brew install python@3.12

# If you get permission errors, fix them first:
sudo chown -R $(whoami) /usr/local/share/zsh /usr/local/share/zsh/site-functions
chmod u+w /usr/local/share/zsh /usr/local/share/zsh/site-functions

# Then try again:
brew install python@3.12
```

### Option B: Using pyenv (If you have it)

```bash
# Install Python 3.12
pyenv install 3.12.7

# Set it as local version for this project
cd /Users/pavery/dev/recipes-etl
pyenv local 3.12.7
```

### Option C: Download from python.org

1. Visit https://www.python.org/downloads/
2. Download Python 3.12.x for macOS
3. Run the installer

## Step 2: Create New Virtual Environment

Once Python 3.12 is installed:

```bash
cd /Users/pavery/dev/recipes-etl

# Remove old venv (optional - you can keep it as backup)
# rm -rf venv

# Create new venv with Python 3.12
python3.12 -m venv venv

# Activate it
source venv/bin/activate

# Verify Python version
python --version
# Should show: Python 3.12.x
```

## Step 3: Install Dependencies

```bash
# Make sure venv is activated
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Install sentence-transformers (this should work now!)
pip install sentence-transformers
```

## Step 4: Verify Installation

```bash
# Test that sentence-transformers works
python -c "from sentence_transformers import SentenceTransformer; print('✅ sentence-transformers installed successfully!')"

# Test the CLI
python -m recipes.cli --help
```

## Step 5: Reindex Elasticsearch with Embeddings

Now you can reindex with embeddings:

```bash
source activate.sh
python -m recipes.cli sync-search --recreate-index
```

## Troubleshooting

### "python3.12: command not found"

Python 3.12 isn't installed or isn't in your PATH. Try:
- Check installation: `brew list python@3.12` or `which python3.12`
- Add to PATH if needed (Homebrew usually does this automatically)
- Restart your terminal

### "Permission denied" with Homebrew

Fix permissions:
```bash
sudo chown -R $(whoami) /usr/local/share/zsh /usr/local/share/zsh/site-functions
chmod u+w /usr/local/share/zsh /usr/local/share/zsh/site-functions
```

### Still having issues?

You can continue using Python 3.13 without embeddings - the code works fine, you just won't have semantic search capabilities until PyTorch supports Python 3.13.

## Quick Reference

```bash
# Full setup from scratch
cd /Users/pavery/dev/recipes-etl
brew install python@3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install sentence-transformers
python -m recipes.cli sync-search --recreate-index
```

