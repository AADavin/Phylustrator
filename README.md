# Phylustrator

A libary for easy plotting of phylogenies

![Phylustrator Example](https://github.com/AADavin/Phylustrator/blob/main/examples/figures/vertical_tree.png))
![Phylustrator Example](https://github.com/AADavin/Phylustrator/blob/main/examples/figures/radial_tree.png))

##  Installation

Phylustrator is pure Python, but it relies on **Cairo** for high-resolution image export.

### Step 1: Install System Libraries (Only for PNG/PDF)
*If you only need SVG output, you can skip this!*

* **Conda (Recommended):**
    ```bash
    conda install -c conda-forge cairo pango
    ```
* **Ubuntu/Debian:** `sudo apt-get install libcairo2-dev`
* **macOS (Homebrew):** `brew install cairo`

### Step 2: Install Phylustrator
You can install the latest version directly from GitHub using pip:

pip install git+[https://github.com/aadria/Phylustrator.git](https://github.com/aadria/Phylustrator.git)
