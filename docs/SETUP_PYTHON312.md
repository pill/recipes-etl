# Setup Python 3.12 Virtual Environment

Run these commands in your terminal (not through the assistant):

## Step 1: Fix Homebrew Permissions (if needed)

```bash
sudo chown -R $(whoami) /usr/local/share/zsh /usr/local/share/zsh/site-functions
chmod u+w /usr/local/share/zsh /usr/local/share/zsh/site-functions
```

## Step 2: Install Python 3.12

```bash
brew install python@3.12
```

This installs Python 3.12 but doesn't make it system-wide - you'll only use it for this project's venv.

## Step 3: Create New Virtual Environment

```bash
cd /Users/pavery/dev/recipes-etl

# Backup old venv (already done)
# mv venv venv.backup.3.13

# Create new venv with Python 3.12
python3.12 -m venv venv

# If python3.12 isn't in PATH, use full path:
# /usr/local/opt/python@3.12/bin/python3.12 -m venv venv
```

## Step 4: Activate and Install Dependencies

```bash
# Activate the new venv
source venv/bin/activate

# Verify Python version
python --version
# Should show: Python 3.12.x

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt

# Install sentence-transformers (this should work now!)
pip install sentence-transformers
```

## Step 5: Verify Everything Works

```bash
# Test sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; print('✅ sentence-transformers works!')"

# Test CLI
python -m recipes.cli --help
```

## Step 6: Reindex with Embeddings

```bash
source activate.sh
python -m recipes.cli sync-search --recreate-index
```

## Troubleshooting

### "python3.12: command not found"

After installing via Homebrew, you may need to:
1. Restart your terminal, or
2. Use the full path: `/usr/local/opt/python@3.12/bin/python3.12 -m venv venv`

### "Permission denied" errors

Run the permission fix commands from Step 1.

### Still having issues?

You can continue using Python 3.13 without embeddings - the code works fine, you just won't have semantic search.

