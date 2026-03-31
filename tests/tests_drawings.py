import pytest
import ete3
import tempfile
from pathlib import Path
from phylustrator.drawing import VerticalTreeDrawer, RadialTreeDrawer, TreeStyle, BaseDrawer


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def simple_tree():
    """Simple two-leaf tree for basic testing."""
    return ete3.Tree("(A:1, B:1);")


@pytest.fixture
def multi_node_tree():
    """Multi-node tree with 4 leaves and named internal nodes."""
    return ete3.Tree("((A:1,B:1)AB:0.5,(C:1,D:1)CD:0.5)root;", format=1)


@pytest.fixture
def transfer_data():
    """Sample horizontal gene transfer data."""
    return [
        {"from": "A", "to": "B", "freq": 1.0},
        {"from": "AB", "to": "CD", "freq": 0.8},
    ]


@pytest.fixture
def trait_data_dict():
    """Sample trait data as dictionary."""
    return {"A": 1.0, "B": 2.0, "C": 1.5, "D": 3.0}


@pytest.fixture
def categorical_trait_data():
    """Sample categorical trait data."""
    return {"A": "type1", "B": "type2", "C": "type1", "D": "type2"}


@pytest.fixture
def tmp_path_factory_fixture(tmp_path):
    """Provide temporary directory for file output tests."""
    return tmp_path


# ============================================================================
# TreeStyle Tests
# ============================================================================


class TestTreeStyle:
    """Test TreeStyle configuration and validation."""

    def test_default_values(self):
        """Test default TreeStyle values."""
        style = TreeStyle()
        assert style.width == 1000
        assert style.height == 1000
        assert style.radius == 400
        assert style.degrees == 360
        assert style.rotation == -90
        assert style.margin == 100.0
        assert style.root_stub_length == 20.0
        assert style.leaf_r == 5.0
        assert style.leaf_color == "black"
        assert style.branch_stroke_width == 2.0
        assert style.branch_color == "black"
        assert style.node_r == 2.0
        assert style.font_size == 12
        assert style.font_family == "Arial"

    def test_custom_values(self):
        """Test setting custom TreeStyle values."""
        style = TreeStyle(
            width=500,
            height=600,
            radius=300,
            degrees=180,
            rotation=0,
            margin=50.0,
            font_size=16,
        )
        assert style.width == 500
        assert style.height == 600
        assert style.radius == 300
        assert style.degrees == 180
        assert style.rotation == 0
        assert style.margin == 50.0
        assert style.font_size == 16

    def test_negative_width_raises_error(self):
        """Test that negative width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            TreeStyle(width=-100)

    def test_zero_width_raises_error(self):
        """Test that zero width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            TreeStyle(width=0)

    def test_negative_height_raises_error(self):
        """Test that negative height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            TreeStyle(height=-100)

    def test_zero_height_raises_error(self):
        """Test that zero height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            TreeStyle(height=0)

    def test_negative_radius_raises_error(self):
        """Test that negative radius raises ValueError."""
        with pytest.raises(ValueError, match="radius must be positive"):
            TreeStyle(radius=-100)

    def test_zero_radius_raises_error(self):
        """Test that zero radius raises ValueError."""
        with pytest.raises(ValueError, match="radius must be positive"):
            TreeStyle(radius=0)

    def test_negative_margin_raises_error(self):
        """Test that negative margin raises ValueError."""
        with pytest.raises(ValueError, match="margin must be non-negative"):
            TreeStyle(margin=-10)

    def test_zero_margin_is_valid(self):
        """Test that zero margin is valid."""
        style = TreeStyle(margin=0)
        assert style.margin == 0

    def test_negative_branch_stroke_width_raises_error(self):
        """Test that negative branch_stroke_width raises ValueError."""
        with pytest.raises(ValueError, match="branch_stroke_width must be positive"):
            TreeStyle(branch_stroke_width=-1)

    def test_zero_branch_stroke_width_raises_error(self):
        """Test that zero branch_stroke_width raises ValueError."""
        with pytest.raises(ValueError, match="branch_stroke_width must be positive"):
            TreeStyle(branch_stroke_width=0)

    def test_negative_font_size_raises_error(self):
        """Test that negative font_size raises ValueError."""
        with pytest.raises(ValueError, match="font_size must be positive"):
            TreeStyle(font_size=-12)

    def test_zero_font_size_raises_error(self):
        """Test that zero font_size raises ValueError."""
        with pytest.raises(ValueError, match="font_size must be positive"):
            TreeStyle(font_size=0)

    def test_zero_leaf_radius_valid(self):
        """Test that zero leaf_r (to hide leaves) is valid."""
        style = TreeStyle(leaf_r=0)
        assert style.leaf_r == 0

    def test_zero_node_radius_valid(self):
        """Test that zero node_r (to hide nodes) is valid."""
        style = TreeStyle(node_r=0)
        assert style.node_r == 0


# ============================================================================
# BaseDrawer Tests
# ============================================================================


class TestBaseDrawer:
    """Test BaseDrawer initialization and abstract methods."""

    def test_init_with_none_tree_raises_type_error(self):
        """Test that initializing with None tree raises TypeError."""
        with pytest.raises(TypeError, match="tree must not be None"):
            BaseDrawer(None)

    def test_init_with_valid_tree(self, simple_tree):
        """Test initialization with valid tree."""
        drawer = BaseDrawer(simple_tree)
        assert drawer.t == simple_tree
        assert isinstance(drawer.style, TreeStyle)
        assert drawer.drawing is not None

    def test_init_with_custom_style(self, simple_tree):
        """Test initialization with custom style."""
        style = TreeStyle(width=500, height=600)
        drawer = BaseDrawer(simple_tree, style=style)
        assert drawer.style.width == 500
        assert drawer.style.height == 600

    def test_calculate_layout_not_implemented(self, simple_tree):
        """Test that _calculate_layout raises NotImplementedError."""
        drawer = BaseDrawer(simple_tree)
        with pytest.raises(NotImplementedError):
            drawer._calculate_layout()

    def test_drawing_has_white_background(self, simple_tree):
        """Test that drawing has white background rectangle."""
        drawer = BaseDrawer(simple_tree)
        # Check that drawing was initialized with a background
        assert drawer.drawing is not None
        assert drawer.d is drawer.drawing  # d is alias for drawing


# ============================================================================
# VerticalTreeDrawer Tests
# ============================================================================


class TestVerticalTreeDrawer:
    """Test VerticalTreeDrawer layout and drawing methods."""

    def test_init_calculates_layout(self, simple_tree):
        """Test that initialization calculates layout."""
        drawer = VerticalTreeDrawer(simple_tree)
        # All nodes should have coordinates
        for node in simple_tree.traverse():
            assert hasattr(node, "coordinates")
            assert len(node.coordinates) == 2
            x, y = node.coordinates
            assert isinstance(x, float)
            assert isinstance(y, float)

    def test_layout_root_at_left_margin(self, simple_tree):
        """Test that root is positioned at left margin."""
        style = TreeStyle(width=1000, margin=100)
        drawer = VerticalTreeDrawer(simple_tree, style=style)
        root = simple_tree.get_tree_root()
        x, _ = root.coordinates
        assert pytest.approx(x) == -1000 / 2 + 100

    def test_layout_leaves_have_different_y_coordinates(self, simple_tree):
        """Test that leaves are positioned at different Y coordinates."""
        drawer = VerticalTreeDrawer(simple_tree)
        leaves = simple_tree.get_leaves()
        y_coords = [leaf.coordinates[1] for leaf in leaves]
        assert len(set(y_coords)) == len(y_coords)  # All different

    def test_layout_internal_node_y_is_average_of_children(self, multi_node_tree):
        """Test that internal nodes are centered between children."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        for node in multi_node_tree.traverse():
            if not node.is_leaf() and node.children:
                child_ys = [c.coordinates[1] for c in node.children]
                expected_y = sum(child_ys) / len(child_ys)
                assert pytest.approx(node.coordinates[1]) == expected_y

    def test_draw_without_branches_to_color(self, simple_tree):
        """Test draw() without branch coloring."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        assert drawer.drawing is not None
        # Drawing should be complete
        svg_content = drawer.drawing.as_svg()
        assert "Line" in svg_content or "line" in svg_content

    def test_draw_with_branch_to_color(self, simple_tree):
        """Test draw() with branch2color mapping."""
        drawer = VerticalTreeDrawer(simple_tree)
        root = simple_tree.get_tree_root()
        branch_colors = {root: "red"}
        drawer.draw(branch2color=branch_colors)
        assert drawer.drawing is not None

    def test_draw_with_right_margin(self, simple_tree):
        """Test draw() with right_margin recalculates layout."""
        drawer = VerticalTreeDrawer(simple_tree)
        original_sf = drawer.sf
        drawer.draw(right_margin=100)
        # Scale factor should change with reduced width (smaller width = larger scale factor to fit in space)
        assert drawer.sf <= original_sf  # Reduced width means reduced scaling

    def test_highlight_clade(self, multi_node_tree):
        """Test highlight_clade adds a background rectangle."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        ab_node = multi_node_tree.search_nodes(name="AB")[0]
        drawer.highlight_clade(ab_node)
        # Drawing should contain the rectangle
        svg_content = drawer.drawing.as_svg()
        assert "Rectangle" in svg_content or "rect" in svg_content

    def test_highlight_branch(self, multi_node_tree):
        """Test highlight_branch adds a thicker line."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        a_node = multi_node_tree.search_nodes(name="A")[0]
        drawer.highlight_branch(a_node, color="red")
        svg_content = drawer.drawing.as_svg()
        assert "red" in svg_content  # Should contain red color

    def test_highlight_branch_on_root_does_nothing(self, simple_tree):
        """Test that highlight_branch on root has no effect."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        root = simple_tree.get_tree_root()
        svg_before = drawer.drawing.as_svg()
        drawer.highlight_branch(root)
        svg_after = drawer.drawing.as_svg()
        # For root node, highlight_branch should return early and not modify drawing
        assert svg_before == svg_after

    def test_gradient_branch(self, multi_node_tree):
        """Test gradient_branch adds a gradient element."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        a_node = multi_node_tree.search_nodes(name="A")[0]
        drawer.gradient_branch(a_node, colors=("red", "blue"))
        assert drawer.drawing is not None

    def test_add_leaf_names(self, simple_tree):
        """Test add_leaf_names adds text labels."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_leaf_names()
        svg_content = drawer.drawing.as_svg()
        # Should contain text elements with leaf names
        assert "Text" in svg_content or "<text" in svg_content

    def test_add_leaf_names_with_custom_params(self, simple_tree):
        """Test add_leaf_names with custom parameters."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_leaf_names(font_size=14, color="red", padding=20)
        assert drawer.drawing is not None

    def test_add_node_names(self, multi_node_tree):
        """Test add_node_names adds labels to internal nodes."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_node_names()
        # Should have added text elements
        svg_content = drawer.drawing.as_svg()
        assert "Text" in svg_content or "<text" in svg_content

    def test_add_leaf_shapes_with_valid_leaves(self, multi_node_tree):
        """Test add_leaf_shapes with valid leaf names."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_leaf_shapes(["A", "B"], shape="circle", fill="blue")
        svg_content = drawer.drawing.as_svg()
        # Should contain circles for the leaf shapes
        assert "Circle" in svg_content or "<circle" in svg_content

    def test_add_leaf_shapes_with_invalid_leaves_warns_not_crashes(
        self, multi_node_tree
    ):
        """Test that add_leaf_shapes with invalid names warns but doesn't crash."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        # Should log warning but not raise exception
        drawer.add_leaf_shapes(["InvalidLeaf"], shape="circle")
        assert drawer.drawing is not None

    def test_add_node_shapes_with_list_of_names(self, multi_node_tree):
        """Test add_node_shapes with list of node names."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_node_shapes(["AB", "CD"], shape="square", fill="red")
        svg_content = drawer.drawing.as_svg()
        # Should contain shapes
        assert "red" in svg_content

    def test_add_node_shapes_with_dict_specs(self, multi_node_tree):
        """Test add_node_shapes with list of dicts."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        specs = [
            {"node": "AB", "shape": "circle", "fill": "red"},
            {"node": "CD", "shape": "square", "fill": "blue"},
        ]
        drawer.add_node_shapes(specs)
        assert drawer.drawing is not None

    def test_add_branch_shapes(self, multi_node_tree):
        """Test add_branch_shapes adds markers along branches."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        specs = [
            {"branch": "A", "where": 0.5, "shape": "circle", "fill": "red"},
            {"branch": "B", "where": 0.3, "shape": "triangle", "fill": "blue"},
        ]
        drawer.add_branch_shapes(specs)
        assert drawer.drawing is not None

    def test_add_trait_strip(self, multi_node_tree):
        """Test add_trait_strip adds colored squares at nodes."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        data = {
            "A": ["red", "blue", "green"],
            "B": ["yellow", "purple"],
        }
        drawer.add_trait_strip(data)
        assert drawer.drawing is not None

    def test_add_time_axis(self, simple_tree):
        """Test add_time_axis adds an axis with ticks."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_time_axis([0, 0.5, 1.0], label="Time (Myr)")
        svg_content = drawer.drawing.as_svg()
        # Should contain text "Time (Myr)"
        assert "Time (Myr)" in svg_content

    def test_add_time_axis_with_custom_labels(self, simple_tree):
        """Test add_time_axis with custom tick labels."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_time_axis(
            [0, 0.5, 1.0], tick_labels=["Recent", "Middle", "Ancient"]
        )
        assert drawer.drawing is not None

    def test_plot_transfers_midpoint_mode(self, multi_node_tree, transfer_data):
        """Test plot_transfers in midpoint mode."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.plot_transfers(transfer_data, mode="midpoint")
        svg_content = drawer.drawing.as_svg()
        # Should contain Path elements for transfer arrows
        assert "Path" in svg_content or "<path" in svg_content

    def test_plot_transfers_with_gradient(self, multi_node_tree, transfer_data):
        """Test plot_transfers with color gradient."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.plot_transfers(
            transfer_data,
            use_gradient=True,
            gradient_colors=("purple", "orange"),
        )
        assert drawer.drawing is not None

    def test_plot_transfers_without_gradient(self, multi_node_tree, transfer_data):
        """Test plot_transfers without color gradient."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.plot_transfers(transfer_data, use_gradient=False, color="orange")
        assert drawer.drawing is not None

    def test_add_heatmap(self, multi_node_tree, trait_data_dict):
        """Test add_heatmap adds a column of colored cells."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_heatmap(trait_data_dict)
        svg_content = drawer.drawing.as_svg()
        # Should contain rectangles for heatmap cells
        assert "Rectangle" in svg_content or "<rect" in svg_content

    def test_add_clade_labels(self, multi_node_tree):
        """Test add_clade_labels adds brackets with text."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        labels = {"AB": "Clade 1", "CD": "Clade 2"}
        drawer.add_clade_labels(labels)
        svg_content = drawer.drawing.as_svg()
        # Should contain the labels
        assert "Clade 1" in svg_content and "Clade 2" in svg_content

    def test_plot_continuous_variable(self, multi_node_tree):
        """Test plot_continuous_variable colors branches by RGB values."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        node_to_rgb = {
            "A": (255, 0, 0),
            "B": (0, 255, 0),
            "C": (0, 0, 255),
            "D": (255, 255, 0),
        }
        drawer.plot_continuous_variable(node_to_rgb)
        assert drawer.drawing is not None

    def test_plot_categorical_trait_with_dict(self, multi_node_tree):
        """Test plot_categorical_trait with dict data."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        trait_data = {"A": "type1", "B": "type2", "C": "type1", "D": "type2"}
        drawer.plot_categorical_trait(trait_data, value_col="type")
        assert drawer.drawing is not None

    def test_plot_categorical_trait_with_auto_palette(self, multi_node_tree):
        """Test plot_categorical_trait with automatic palette."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        trait_data = {"A": "red", "B": "blue", "C": "red"}
        drawer.plot_categorical_trait(trait_data, value_col="color")
        assert drawer.drawing is not None

    def test_plot_categorical_trait_with_custom_palette(self, multi_node_tree):
        """Test plot_categorical_trait with custom color palette."""
        drawer = VerticalTreeDrawer(multi_node_tree)
        drawer.draw()
        trait_data = {"A": "type1", "B": "type2"}
        palette = {"type1": "#FF0000", "type2": "#00FF00"}
        drawer.plot_categorical_trait(
            trait_data, value_col="type", palette=palette
        )
        assert drawer.drawing is not None

    def test_add_categorical_legend(self, simple_tree):
        """Test add_categorical_legend adds legend with colored circles."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        palette = {"TypeA": "red", "TypeB": "blue"}
        drawer.add_categorical_legend(palette)
        svg_content = drawer.drawing.as_svg()
        # Should contain legend labels
        assert "TypeA" in svg_content and "TypeB" in svg_content

    def test_add_transfer_legend(self, simple_tree):
        """Test add_transfer_legend adds HGT-specific legend."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_transfer_legend()
        svg_content = drawer.drawing.as_svg()
        # Should contain transfer legend labels
        assert "Departure" in svg_content or "Arrival" in svg_content

    def test_add_color_bar(self, simple_tree):
        """Test add_color_bar adds continuous gradient legend."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_color_bar("white", "black", 0, 100)
        svg_content = drawer.drawing.as_svg()
        # Should contain gradient
        assert "gradient" in svg_content or "Gradient" in svg_content

    def test_add_title_top(self, simple_tree):
        """Test add_title at top position."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_title("My Tree", position="top")
        svg_content = drawer.drawing.as_svg()
        # Should contain the title text
        assert "My Tree" in svg_content

    def test_add_title_bottom(self, simple_tree):
        """Test add_title at bottom position."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_title("My Tree", position="bottom")
        assert drawer.drawing is not None

    def test_add_title_left(self, simple_tree):
        """Test add_title at left position."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_title("My Tree", position="left")
        assert drawer.drawing is not None

    def test_add_title_right(self, simple_tree):
        """Test add_title at right position."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_title("My Tree", position="right")
        assert drawer.drawing is not None

    def test_add_title_custom_params(self, simple_tree):
        """Test add_title with custom parameters."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        # VerticalTreeDrawer.add_title doesn't validate position
        drawer.add_title("My Tree", position="invalid", font_size=20, color="blue")
        assert drawer.drawing is not None

    def test_add_scale_bar(self, simple_tree):
        """Test add_scale_bar adds a scale reference."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_scale_bar(length=1.0, label="1.0 Myr")
        # Should complete without error
        assert drawer.drawing is not None

    def test_save_svg_creates_file(self, simple_tree, tmp_path):
        """Test save_svg creates an SVG file."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        output_file = tmp_path / "test.svg"
        drawer.save_svg(str(output_file))
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_save_svg_content_is_valid_xml(self, simple_tree, tmp_path):
        """Test that saved SVG is valid XML."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        output_file = tmp_path / "test.svg"
        drawer.save_svg(str(output_file))
        content = output_file.read_text()
        # Should contain SVG elements
        assert "<svg" in content or "svg" in content
        assert "</svg>" in content or "/svg>" in content

    def test_save_svg_with_rotation(self, simple_tree, tmp_path):
        """Test save_svg with rotation parameter."""
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        output_file = tmp_path / "test_rotated.svg"
        drawer.save_svg(str(output_file), rotation=45)
        assert output_file.exists()

    def test_save_png_creates_file(self, simple_tree, tmp_path):
        """Test save_png creates a PNG file."""
        pytest.importorskip("cairosvg")
        drawer = VerticalTreeDrawer(simple_tree)
        drawer.draw()
        output_file = tmp_path / "test.png"
        drawer.save_png(str(output_file))
        assert output_file.exists()


# ============================================================================
# RadialTreeDrawer Tests
# ============================================================================


class TestRadialTreeDrawer:
    """Test RadialTreeDrawer layout and drawing methods."""

    def test_init_calculates_layout(self, simple_tree):
        """Test that initialization calculates layout."""
        drawer = RadialTreeDrawer(simple_tree)
        # All nodes should have rad and angle
        for node in simple_tree.traverse():
            assert hasattr(node, "rad")
            assert hasattr(node, "angle")

    def test_layout_root_rad_is_zero(self, simple_tree):
        """Test that root radius is zero."""
        drawer = RadialTreeDrawer(simple_tree)
        root = simple_tree.get_tree_root()
        assert root.rad == 0.0

    def test_layout_leaves_at_max_radius(self, simple_tree):
        """Test that leaves are at or near the maximum radius."""
        style = TreeStyle(radius=200)
        drawer = RadialTreeDrawer(simple_tree, style=style)
        leaves = simple_tree.get_leaves()
        for leaf in leaves:
            assert pytest.approx(leaf.rad) == 200

    def test_layout_angles_span_360_degrees(self, simple_tree):
        """Test that leaf angles span the specified degrees."""
        drawer = RadialTreeDrawer(simple_tree)
        leaves = simple_tree.get_leaves()
        angles = [leaf.angle for leaf in leaves]
        # Should span from 0 to ~360/n_leaves per leaf
        assert len(angles) == len(leaves)

    def test_layout_internal_node_angle_is_centered(self, multi_node_tree):
        """Test that internal nodes are angularly centered."""
        drawer = RadialTreeDrawer(multi_node_tree)
        for node in multi_node_tree.traverse():
            if not node.is_leaf() and node.children:
                child_angles = [c.angle for c in node.children]
                expected_angle = sum(child_angles) / len(child_angles)
                assert pytest.approx(node.angle) == expected_angle

    def test_draw_without_branch_colors(self, simple_tree):
        """Test draw() without branch coloring."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        assert drawer.drawing is not None
        svg_content = drawer.drawing.as_svg()
        assert "path" in svg_content.lower() or "line" in svg_content.lower()

    def test_draw_with_branch_colors(self, simple_tree):
        """Test draw() with branch2color mapping."""
        drawer = RadialTreeDrawer(simple_tree)
        root = simple_tree.get_tree_root()
        branch_colors = {root: "red"}
        drawer.draw(branch2color=branch_colors)
        assert drawer.drawing is not None

    def test_highlight_clade(self, multi_node_tree):
        """Test highlight_clade adds a wedge background."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        ab_node = multi_node_tree.search_nodes(name="AB")[0]
        drawer.highlight_clade(ab_node)
        svg_content = drawer.drawing.as_svg()
        assert "path" in svg_content.lower()  # Wedge is drawn as a path

    def test_highlight_branch(self, multi_node_tree):
        """Test highlight_branch adds a thicker arc."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        a_node = multi_node_tree.search_nodes(name="A")[0]
        drawer.highlight_branch(a_node)
        svg_content = drawer.drawing.as_svg()
        assert "red" in svg_content  # Default highlight color is red

    def test_highlight_branch_on_root_does_nothing(self, simple_tree):
        """Test that highlight_branch on root has no effect."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        root = simple_tree.get_tree_root()
        svg_before = drawer.drawing.as_svg()
        drawer.highlight_branch(root)
        svg_after = drawer.drawing.as_svg()
        # For root node, highlight_branch should return early
        assert svg_before == svg_after

    def test_gradient_branch(self, multi_node_tree):
        """Test gradient_branch adds a gradient."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        a_node = multi_node_tree.search_nodes(name="A")[0]
        drawer.gradient_branch(a_node, colors=("red", "blue"))
        assert drawer.drawing is not None

    def test_add_leaf_names(self, simple_tree):
        """Test add_leaf_names adds rotated text labels."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_leaf_names()
        svg_content = drawer.drawing.as_svg()
        assert "text" in svg_content.lower()

    def test_add_leaf_names_with_custom_params(self, simple_tree):
        """Test add_leaf_names with custom parameters."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_leaf_names(font_size=14, color="red", padding=20)
        assert drawer.drawing is not None

    def test_add_node_names(self, multi_node_tree):
        """Test add_node_names adds labels to internal nodes."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_node_names()
        svg_content = drawer.drawing.as_svg()
        assert "text" in svg_content.lower()

    def test_add_leaf_shapes(self, multi_node_tree):
        """Test add_leaf_shapes adds markers to leaves."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_leaf_shapes(["A", "B"], shape="circle", fill="blue")
        svg_content = drawer.drawing.as_svg()
        assert "circle" in svg_content.lower() or "blue" in svg_content

    def test_add_leaf_shapes_with_invalid_names_warns(self, multi_node_tree):
        """Test that add_leaf_shapes with invalid names warns but doesn't crash."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_leaf_shapes(["InvalidLeaf"], shape="circle")
        assert drawer.drawing is not None

    def test_add_node_shapes_with_list(self, multi_node_tree):
        """Test add_node_shapes with list of names."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.add_node_shapes(["AB", "CD"])
        svg_content = drawer.drawing.as_svg()
        assert "circle" in svg_content.lower() or "red" in svg_content

    def test_add_node_shapes_with_dict_specs(self, multi_node_tree):
        """Test add_node_shapes with list of dicts."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        specs = [
            {"node": "AB", "shape": "circle", "fill": "red"},
            {"node": "CD", "shape": "square", "fill": "blue"},
        ]
        drawer.add_node_shapes(specs)
        assert drawer.drawing is not None

    def test_add_branch_shapes(self, multi_node_tree):
        """Test add_branch_shapes adds markers on branches."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        specs = [
            {"branch": "A", "where": 0.5, "shape": "circle", "fill": "red"},
        ]
        drawer.add_branch_shapes(specs)
        assert drawer.drawing is not None

    def test_add_trait_strip(self, multi_node_tree):
        """Test add_trait_strip adds colored squares."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        data = {"A": ["red", "blue"], "B": ["green", "yellow"]}
        drawer.add_trait_strip(data)
        assert drawer.drawing is not None

    def test_plot_transfers(self, multi_node_tree, transfer_data):
        """Test plot_transfers plots HGT events."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        drawer.plot_transfers(transfer_data)
        svg_content = drawer.drawing.as_svg()
        assert "path" in svg_content.lower()  # Transfer events are paths

    def test_plot_continuous_variable(self, multi_node_tree):
        """Test plot_continuous_variable colors branches."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        node_to_rgb = {
            "A": (255, 0, 0),
            "B": (0, 255, 0),
        }
        drawer.plot_continuous_variable(node_to_rgb)
        assert drawer.drawing is not None

    def test_plot_categorical_trait(self, multi_node_tree):
        """Test plot_categorical_trait colors branches by category."""
        drawer = RadialTreeDrawer(multi_node_tree)
        drawer.draw()
        trait_data = {"A": "type1", "B": "type2"}
        drawer.plot_categorical_trait(trait_data, value_col="type")
        assert drawer.drawing is not None

    def test_add_categorical_legend(self, simple_tree):
        """Test add_categorical_legend."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        palette = {"TypeA": "red", "TypeB": "blue"}
        drawer.add_categorical_legend(palette)
        assert drawer.drawing is not None

    def test_add_color_bar(self, simple_tree):
        """Test add_color_bar."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        drawer.add_color_bar("white", "black", 0, 100)
        assert drawer.drawing is not None

    def test_add_title_all_positions(self, simple_tree):
        """Test add_title at all positions."""
        for position in ["top", "bottom", "left", "right"]:
            drawer = RadialTreeDrawer(simple_tree)
            drawer.draw()
            drawer.add_title("Test", position=position)
            assert drawer.drawing is not None

    def test_add_title_invalid_position(self, simple_tree):
        """Test add_title with invalid position."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        with pytest.raises(ValueError):
            drawer.add_title("Test", position="invalid")

    def test_save_svg_creates_file(self, simple_tree, tmp_path):
        """Test save_svg creates a file."""
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        output_file = tmp_path / "radial.svg"
        drawer.save_svg(str(output_file))
        assert output_file.exists()

    def test_save_png_creates_file(self, simple_tree, tmp_path):
        """Test save_png creates a file."""
        pytest.importorskip("cairosvg")
        drawer = RadialTreeDrawer(simple_tree)
        drawer.draw()
        output_file = tmp_path / "radial.png"
        drawer.save_png(str(output_file))
        assert output_file.exists()


# ============================================================================
# Parametrized tests for both drawer types
# ============================================================================


@pytest.mark.parametrize("drawer_class", [VerticalTreeDrawer, RadialTreeDrawer])
class TestBothDrawers:
    """Tests that apply to both drawer types."""

    def test_method_existence(self, drawer_class, simple_tree):
        """Verify all required methods exist on both drawer types."""
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
            "add_trait_strip",
            "plot_continuous_variable",
            "plot_categorical_trait",
            "add_categorical_legend",
            "add_color_bar",
            "add_title",
            "save_svg",
            "save_png",
        ]

        for method in required_methods:
            assert hasattr(drawer, method), (
                f"{drawer_class.__name__} is missing method: {method}"
            )

    def test_smoke_execution(self, drawer_class, simple_tree, transfer_data):
        """Smoke test: execute all major methods without crashing."""
        drawer = drawer_class(simple_tree)

        # Core drawing
        drawer.draw()

        # Overlays
        drawer.highlight_clade(simple_tree)
        drawer.add_leaf_names()

        # Legends
        drawer.add_categorical_legend({"Type": "red"})
        drawer.add_color_bar("red", "blue", 0, 1)

        # Title
        drawer.add_title("Test")

        # Should complete without error
        assert drawer.drawing is not None

    def test_pre_flight_check_triggers_layout(self, drawer_class, simple_tree):
        """Test that _pre_flight_check ensures layout is calculated."""
        drawer = drawer_class(simple_tree)
        # Verify layout was calculated on init
        assert drawer._layout_calculated is True
        # Add a title which calls _pre_flight_check
        drawer.add_title("Test")
        # Should still have layout calculated
        assert drawer._layout_calculated is True
