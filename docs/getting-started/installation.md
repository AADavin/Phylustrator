# Installation Guide

This guide covers installing Phylustrator and its optional dependencies.

## Prerequisites

- Python 3.8 or higher
- pip or conda package manager

## Basic Installation

Install the latest version directly from GitHub using pip:

```bash
pip install git+https://github.com/AADavin/Phylustrator.git
```

## System Dependencies (Optional)

Phylustrator is pure Python, but it relies on **Cairo** for high-resolution image export (PNG and PDF formats). If you only need SVG output, you can skip this section.

### Windows

Install Cairo using conda (recommended):

```bash
conda install -c conda-forge cairo pango
```

### macOS

Use Homebrew:

```bash
brew install cairo
```

Then install Phylustrator:

```bash
pip install git+https://github.com/AADavin/Phylustrator.git
```

### Linux (Ubuntu/Debian)

Install system libraries:

```bash
sudo apt-get install libcairo2-dev
```

Then install Phylustrator:

```bash
pip install git+https://github.com/AADavin/Phylustrator.git
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install cairo-devel
```

Then install Phylustrator:

```bash
pip install git+https://github.com/AADavin/Phylustrator.git
```

## Installation with Export Support

To enable PNG and PDF export, install the optional export dependencies:

```bash
pip install git+https://github.com/AADavin/Phylustrator.git[export]
```

This will automatically install `cairosvg` alongside Phylustrator.

## Development Installation

If you want to contribute to Phylustrator, clone the repository and install in development mode:

```bash
git clone https://github.com/AADavin/Phylustrator.git
cd Phylustrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Verify Installation

To verify that Phylustrator is installed correctly, run:

```python
import phylustrator as ph
print(ph.__version__)
```

You should see version information printed. If you installed export support, you can also test PNG export:

```python
import ete3
import phylustrator as ph

# Create a simple tree
t = ete3.Tree("(A:1,B:1)C;", format=1)
style = ph.TreeStyle(width=400, height=400)
drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.save_png("test.png")  # Should work without errors
```

## Troubleshooting

### ImportError: cairosvg not found

If you get this error when trying to save PNG/PDF files:

```
ImportError: PNG export requires 'cairosvg'. Install it with: pip install phylustrator[export]
```

Install the export dependencies:

```bash
pip install git+https://github.com/AADavin/Phylustrator.git[export]
```

### Cairo installation issues

If you're having trouble installing Cairo system libraries:

1. Try conda instead of system package managers:
   ```bash
   conda install -c conda-forge cairo pango
   ```

2. On macOS, ensure Homebrew is properly configured:
   ```bash
   brew doctor
   ```

3. On Linux, try installing the development libraries:
   ```bash
   sudo apt-get install libcairo2-dev  # Ubuntu/Debian
   ```

### ete3 import errors

Phylustrator uses ete3 for tree handling. If you have issues with ete3:

```bash
pip install ete3
```

## Next Steps

Once installed, check out the [Quick Start](quickstart.md) guide to create your first tree visualization.
