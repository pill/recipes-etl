# Installing Embedding Dependencies

This guide helps you install `sentence-transformers` for vector embeddings, especially if you encounter issues with PyTorch (torch) on Python 3.13.

## ⚠️ Important: Python 3.13 Limitation

**PyTorch (torch) is not yet available for Python 3.13.** Since `sentence-transformers` requires torch, embeddings are **not available on Python 3.13** at this time.

**Solutions:**
- Use **Python 3.11 or 3.12** if you need embeddings (recommended)
- Or skip embeddings for now - the code works fine without them

## The Problem

`sentence-transformers` requires `torch` (PyTorch), which does not have pre-built wheels for Python 3.13 yet. This causes installation failures.

## Solutions

### Option 1: Use Python 3.11 or 3.12 (Recommended - Only Working Solution)

**This is the only way to get embeddings working currently.** PyTorch doesn't support Python 3.13 yet.

```bash
# Create a new virtual environment with Python 3.11 or 3.12
python3.11 -m venv venv
# or
python3.12 -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt
pip install sentence-transformers
```

**Note:** If you don't have Python 3.11 or 3.12 installed:
- **macOS**: `brew install python@3.11` or `brew install python@3.12`
- **Linux**: Use your package manager or pyenv
- **Windows**: Download from python.org

### Option 2: Skip embeddings entirely (Works on Python 3.13)

If you don't need embeddings right now, you can skip installation. The code will work without embeddings - recipes will just be indexed without vector embeddings in Elasticsearch.

## Verify Installation

After installing, verify it works:

```python
python3 -c "from sentence_transformers import SentenceTransformer; print('✅ sentence-transformers installed successfully')"
```

## Reindexing After Installation

Once `sentence-transformers` is installed, you can reindex Elasticsearch with embeddings:

```bash
source activate.sh
python -m recipes.cli sync-search --recreate-index
```

## Troubleshooting

### "No module named 'sentence_transformers'"

The module isn't installed. Try one of the options above.

### "torch not found" or similar errors

This means torch isn't available for your Python version. **You must use Python 3.11 or 3.12** - there's no workaround for Python 3.13 at this time.

### Slow embedding generation

If embeddings are slow, you're likely using CPU-only mode (no torch). This is normal and acceptable for most use cases. For faster performance, use Python 3.11/3.12 with full torch support.

## Performance Notes

- **With torch (GPU/CPU optimized)**: Fast embedding generation
- **Without torch (CPU-only)**: Slower but still functional
- **No embeddings**: Fastest indexing, but no semantic search capability

Choose based on your needs!

