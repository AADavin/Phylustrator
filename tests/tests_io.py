"""Tests for the io module."""

import pytest
import tempfile
from pathlib import Path
from phylustrator.io import read_tree, read_newick, read_nexus, read_phyloxml


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def basic_tree_path():
    """Path to the basic tree.nwk example file."""
    return Path(__file__).parent.parent / "examples/data/basic/tree.nwk"


@pytest.fixture
def nexus_content():
    """Sample Nexus format content."""
    return """#NEXUS
begin taxa;
  ntax=4;
  taxlabels
    species1
    species2
    species3
    species4
  ;
end;

begin trees;
  tree tree1 = (species1:1.0,(species2:0.5,(species3:0.3,species4:0.3):0.2):0.5);
  tree tree2 = ((species1:0.5,species2:0.5):0.5,(species3:0.5,species4:0.5):0.5);
end;
"""


@pytest.fixture
def phyloxml_content():
    """Sample PhyloXML format content."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<phyloxml xmlns="http://www.phyloxml.org">
  <phylogeny>
    <name>Example tree</name>
    <clade>
      <name>root</name>
      <branch_length>0.0</branch_length>
      <clade>
        <name>A</name>
        <branch_length>1.0</branch_length>
      </clade>
      <clade>
        <name>B</name>
        <branch_length>1.0</branch_length>
      </clade>
    </clade>
  </phylogeny>
</phyloxml>
"""


# ============================================================================
# Tests for read_newick
# ============================================================================


def test_read_newick_from_file(basic_tree_path):
    """Test reading a Newick format tree from file."""
    tree = read_newick(basic_tree_path)
    assert tree is not None
    assert len(tree) > 0  # Has leaves
    assert tree.get_leaves()  # Can get leaves


def test_read_newick_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_newick("/nonexistent/path/tree.nwk")


# ============================================================================
# Tests for read_nexus
# ============================================================================


def test_read_nexus_from_string(nexus_content):
    """Test reading a Nexus format tree from a temp file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nexus_path = Path(tmpdir) / "test.nex"
        nexus_path.write_text(nexus_content)

        tree = read_nexus(nexus_path)
        assert tree is not None
        assert len(tree) > 0
        assert tree.get_leaves()


def test_read_nexus_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_nexus("/nonexistent/path/tree.nex")


def test_read_nexus_invalid_format(tmp_path):
    """Test that invalid Nexus format raises ValueError."""
    invalid_nexus = tmp_path / "invalid.nex"
    invalid_nexus.write_text("This is not valid Nexus format")

    with pytest.raises(ValueError, match="No 'begin trees;' block found"):
        read_nexus(invalid_nexus)


def test_read_nexus_multiple_trees(tmp_path):
    """Test reading multiple trees from Nexus file."""
    nexus_content = """#NEXUS
begin trees;
  tree tree1 = (A:1.0,B:1.0);
  tree tree2 = ((A:0.5,B:0.5):0.5);
end;
"""
    nexus_path = tmp_path / "multi.nex"
    nexus_path.write_text(nexus_content)

    # Read first tree
    tree1 = read_nexus(nexus_path, tree_index=0)
    assert tree1 is not None

    # Read second tree
    tree2 = read_nexus(nexus_path, tree_index=1)
    assert tree2 is not None


def test_read_nexus_invalid_tree_index(tmp_path):
    """Test that invalid tree index raises ValueError."""
    nexus_content = """#NEXUS
begin trees;
  tree tree1 = (A:1.0,B:1.0);
end;
"""
    nexus_path = tmp_path / "single.nex"
    nexus_path.write_text(nexus_content)

    with pytest.raises(ValueError, match="Tree index .* out of range"):
        read_nexus(nexus_path, tree_index=5)


# ============================================================================
# Tests for read_phyloxml
# ============================================================================


def test_read_phyloxml_from_string(phyloxml_content):
    """Test reading a PhyloXML format tree from a temp file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        xml_path = Path(tmpdir) / "test.xml"
        xml_path.write_text(phyloxml_content)

        tree = read_phyloxml(xml_path)
        assert tree is not None
        assert len(tree) >= 2  # Has at least root + 2 children


def test_read_phyloxml_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_phyloxml("/nonexistent/path/tree.xml")


def test_read_phyloxml_invalid_format(tmp_path):
    """Test that invalid XML raises ValueError."""
    invalid_xml = tmp_path / "invalid.xml"
    invalid_xml.write_text("This is not valid XML <unclosed>")

    with pytest.raises(ValueError, match="Invalid XML"):
        read_phyloxml(invalid_xml)


def test_read_phyloxml_missing_clade(tmp_path):
    """Test that XML without clade element raises ValueError."""
    invalid_phyloxml = tmp_path / "no_clade.xml"
    invalid_phyloxml.write_text("""<?xml version="1.0"?>
<phyloxml xmlns="http://www.phyloxml.org">
  <phylogeny>
    <name>No clade here</name>
  </phylogeny>
</phyloxml>
""")

    with pytest.raises(ValueError, match="No clade element found"):
        read_phyloxml(invalid_phyloxml)


# ============================================================================
# Tests for read_tree (auto-detection)
# ============================================================================


def test_read_tree_auto_detect_newick(basic_tree_path):
    """Test auto-detection of Newick format by extension."""
    tree = read_tree(basic_tree_path)
    assert tree is not None
    assert len(tree) > 0


def test_read_tree_auto_detect_nexus(nexus_content):
    """Test auto-detection of Nexus format by .nex extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nexus_path = Path(tmpdir) / "test.nex"
        nexus_path.write_text(nexus_content)

        tree = read_tree(nexus_path)
        assert tree is not None
        assert len(tree) > 0


def test_read_tree_auto_detect_phyloxml(phyloxml_content):
    """Test auto-detection of PhyloXML format by .xml extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        xml_path = Path(tmpdir) / "test.xml"
        xml_path.write_text(phyloxml_content)

        tree = read_tree(xml_path)
        assert tree is not None
        assert len(tree) >= 2


def test_read_tree_explicit_format(basic_tree_path):
    """Test reading with explicit format specification."""
    tree = read_tree(basic_tree_path, format="newick")
    assert tree is not None


def test_read_tree_invalid_format(basic_tree_path):
    """Test that invalid format raises ValueError."""
    with pytest.raises(ValueError, match="Unknown format"):
        read_tree(basic_tree_path, format="fasta")


def test_read_tree_unknown_extension(tmp_path):
    """Test that unknown extension raises ValueError."""
    unknown_file = tmp_path / "tree.unknown"
    unknown_file.write_text("(A:1.0,B:1.0);")

    with pytest.raises(ValueError, match="Could not determine format"):
        read_tree(unknown_file)


def test_read_tree_unknown_extension_explicit_format(tmp_path):
    """Test that unknown extension can be overridden with explicit format."""
    newick_file = tmp_path / "tree.unknown"
    newick_file.write_text("(A:1.0,B:1.0);")

    tree = read_tree(newick_file, format="newick")
    assert tree is not None


def test_read_tree_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_tree("/nonexistent/path/tree.nwk")


# ============================================================================
# Additional edge cases
# ============================================================================


def test_read_newick_with_newick_format_kwarg(basic_tree_path):
    """Test that newick_format kwarg is passed through."""
    tree = read_newick(basic_tree_path, newick_format=1)
    assert tree is not None


def test_read_tree_pathlib_path(basic_tree_path):
    """Test that pathlib.Path objects are supported."""
    tree = read_tree(Path(basic_tree_path))
    assert tree is not None


def test_read_tree_string_path(basic_tree_path):
    """Test that string paths are supported."""
    tree = read_tree(str(basic_tree_path))
    assert tree is not None
