import pytest
import ete3
from phylustrator.drawing import VerticalTreeDrawer, RadialTreeDrawer, TreeStyle

@pytest.fixture
def simple_tree():
    # Simple tree: (A:1, B:1);
    return ete3.Tree("(A:1, B:1);")

@pytest.fixture
def transfer_data():
    return [{"from": "A", "to": "B", "freq": 1.0}]

@pytest.fixture
def trait_data():
    return {"A": 1.0, "B": 2.0}

def test_vertical_layout_init(simple_tree):
    style = TreeStyle(width=500, height=500)
    drawer = VerticalTreeDrawer(simple_tree, style=style)
    
    # Check if layout was calculated
    for node in simple_tree.traverse():
        assert hasattr(node, "coordinates")
        assert len(node.coordinates) == 2

def test_radial_layout_init(simple_tree):
    style = TreeStyle(radius=200)
    drawer = RadialTreeDrawer(simple_tree, style=style)
    
    # Check if layout was calculated
    for node in simple_tree.traverse():
        assert hasattr(node, "rad")
        assert hasattr(node, "angle")
        
    # Check bounds
    root = simple_tree.get_tree_root()
    assert root.rad == 0
    leaf_a = simple_tree.search_nodes(name="A")[0]
    assert leaf_a.rad == 200

def test_pre_flight_check(simple_tree):
    drawer = VerticalTreeDrawer(simple_tree)
    # Reset flag manually
    drawer._layout_calculated = False
    # Calling a method that triggers check
    drawer.add_title("Test")
    assert drawer._layout_calculated is True

@pytest.mark.parametrize("drawer_class", [VerticalTreeDrawer, RadialTreeDrawer])
def test_method_existence(drawer_class, simple_tree):
    """
    Comprehensive existence check for all public API methods to prevent 
    regressions during refactoring.
    """
    drawer = drawer_class(simple_tree)
    
    required_methods = [
        "draw",
        "highlight_clade",
        "highlight_branch",
        "gradient_branch",
        "add_leaf_names",
        "add_node_names",
        "add_leaf_shapes",
        "add_node_shapes",
        "add_branch_shapes",
        "plot_transfers",
        "add_time_axis",
        "add_heatmap",
        "add_clade_labels",
        "plot_continuous_variable",
        "plot_categorical_trait",
        "add_categorical_legend",
        "add_transfer_legend",
        "add_color_bar",
        "add_leaf_images",
        "add_ancestral_images",
        "add_title",
        "add_scale_bar",
        "save_svg",
        "save_png"
    ]
    
    for method in required_methods:
        assert hasattr(drawer, method), f"{drawer_class.__name__} is missing required method: {method}"

@pytest.mark.parametrize("drawer_class", [VerticalTreeDrawer, RadialTreeDrawer])
def test_smoke_execution(drawer_class, simple_tree, transfer_data, trait_data):
    """
    Executes core methods with dummy data to ensure no internal crashes/SyntaxErrors.
    """
    drawer = drawer_class(simple_tree)
    
    # Core Drawing
    drawer.draw()
    
    # Overlays
    drawer.highlight_clade(simple_tree, color="red")
    drawer.add_leaf_names()
    drawer.add_leaf_shapes(["A"], r=5)
    drawer.add_branch_shapes([{"branch": "A", "where": 0.5, "shape": "circle"}])
    drawer.plot_transfers(transfer_data)
    
    # Labels & Legends
    drawer.add_clade_labels({"A": "Label"})
    drawer.add_categorical_legend({"Trait": "blue"})
    drawer.add_color_bar("white", "blue", 0, 1)
    
    # Traits
    drawer.plot_categorical_trait(trait_data, value_col="trait")
    
    # Title
    drawer.add_title("Smoke Test")
    
    assert drawer.drawing is not None
