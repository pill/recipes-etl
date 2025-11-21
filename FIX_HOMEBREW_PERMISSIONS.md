# Fix Homebrew Permissions

You're getting permission errors installing Python 3.12. Run these commands to fix it:

## Step 1: Fix Homebrew Directory Permissions

```bash
# Fix ownership of Homebrew directories
sudo chown -R $(whoami) /usr/local/Cellar
sudo chown -R $(whoami) /usr/local/opt
sudo chown -R $(whoami) /usr/local/share
sudo chown -R $(whoami) /usr/local/bin
sudo chown -R $(whoami) /usr/local/lib
sudo chown -R $(whoami) /usr/local/include
sudo chown -R $(whoami) /usr/local/Frameworks

# Fix zsh directories (from earlier error)
sudo chown -R $(whoami) /usr/local/share/zsh
sudo chown -R $(whoami) /usr/local/share/zsh/site-functions
chmod u+w /usr/local/share/zsh /usr/local/share/zsh/site-functions
```

## Step 2: Try Installing Python 3.12 Again

```bash
brew install python@3.12
```

## Alternative: If Permissions Keep Failing

If you continue having permission issues, you can:

### Option A: Use Homebrew's recommended fix

```bash
# Let Homebrew fix itself
sudo chown -R $(whoami) $(brew --prefix)/*
```

### Option B: Install Python 3.12 from python.org (No Homebrew needed)

1. Download Python 3.12 from: https://www.python.org/downloads/release/python-3127/
2. Run the installer (it installs to `/Library/Frameworks/Python.framework/`)
3. Then create venv with: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m venv venv`

### Option C: Use pyenv (Python version manager)

```bash
# Install pyenv
brew install pyenv

# Add to your shell profile (~/.zshrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload shell
source ~/.zshrc

# Install Python 3.12 via pyenv
pyenv install 3.12.7

# Use it for this project
cd /Users/pavery/dev/recipes-etl
pyenv local 3.12.7

# Create venv
python -m venv venv
```

## Quick Fix (Try This First)

The quickest fix is usually:

```bash
sudo chown -R $(whoami) $(brew --prefix)/*
brew install python@3.12
```

