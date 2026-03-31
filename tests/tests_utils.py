import pytest
import math
from phylustrator.utils import (
    to_rgb,
    to_hex,
    lerp_color,
    polar_to_cartesian,
    generate_id,
    add_origin_if_root_has_dist,
)
import ete3


class TestToRgb:
    """Test color string to RGB tuple conversion."""

    def test_hex_6_digit_uppercase(self):
        """Test parsing 6-digit hex code with uppercase letters."""
        assert to_rgb("#FFFFFF") == (255, 255, 255)
        assert to_rgb("#FF0000") == (255, 0, 0)
        assert to_rgb("#00FF00") == (0, 255, 0)

    def test_hex_6_digit_lowercase(self):
        """Test parsing 6-digit hex code with lowercase letters."""
        assert to_rgb("#ffffff") == (255, 255, 255)
        assert to_rgb("#ff0000") == (255, 0, 0)
        assert to_rgb("#00ff00") == (0, 255, 0)

    def test_hex_6_digit_mixed_case(self):
        """Test parsing 6-digit hex code with mixed case."""
        assert to_rgb("#AbCdEf") == (171, 205, 239)
        assert to_rgb("#123abc") == (18, 58, 188)

    def test_hex_3_digit(self):
        """Test parsing 3-digit hex code (shorthand)."""
        assert to_rgb("#fff") == (255, 255, 255)
        assert to_rgb("#000") == (0, 0, 0)
        assert to_rgb("#f00") == (255, 0, 0)
        assert to_rgb("#0f0") == (0, 255, 0)
        assert to_rgb("#00f") == (0, 0, 255)

    def test_hex_3_digit_mixed_case(self):
        """Test parsing 3-digit hex code with mixed case."""
        assert to_rgb("#AbC") == (170, 187, 204)
        assert to_rgb("#FfF") == (255, 255, 255)

    def test_named_colors_basic(self):
        """Test common CSS named colors."""
        assert to_rgb("white") == (255, 255, 255)
        assert to_rgb("black") == (0, 0, 0)
        assert to_rgb("red") == (255, 0, 0)
        assert to_rgb("green") == (0, 128, 0)
        assert to_rgb("blue") == (0, 0, 255)
        assert to_rgb("yellow") == (255, 255, 0)

    def test_named_colors_extended(self):
        """Test extended set of CSS named colors."""
        assert to_rgb("orange") == (255, 165, 0)
        assert to_rgb("purple") == (128, 0, 128)
        assert to_rgb("gray") == (128, 128, 128)
        assert to_rgb("grey") == (128, 128, 128)
        assert to_rgb("cyan") == (0, 255, 255)
        assert to_rgb("magenta") == (255, 0, 255)
        assert to_rgb("brown") == (165, 42, 42)
        assert to_rgb("pink") == (255, 192, 203)
        assert to_rgb("lime") == (0, 255, 0)
        assert to_rgb("navy") == (0, 0, 128)
        assert to_rgb("teal") == (0, 128, 128)
        assert to_rgb("maroon") == (128, 0, 0)
        assert to_rgb("olive") == (128, 128, 0)
        assert to_rgb("coral") == (255, 127, 80)
        assert to_rgb("salmon") == (250, 128, 114)
        assert to_rgb("gold") == (255, 215, 0)
        assert to_rgb("darkgreen") == (0, 100, 0)
        assert to_rgb("darkblue") == (0, 0, 139)
        assert to_rgb("darkred") == (139, 0, 0)
        assert to_rgb("lightblue") == (173, 216, 230)
        assert to_rgb("lightgreen") == (144, 238, 144)
        assert to_rgb("lightgray") == (211, 211, 211)
        assert to_rgb("lightgrey") == (211, 211, 211)

    def test_named_colors_case_insensitive(self):
        """Test that named colors are case insensitive."""
        assert to_rgb("RED") == (255, 0, 0)
        assert to_rgb("Blue") == (0, 0, 255)
        assert to_rgb("GrEeN") == (0, 128, 0)

    def test_invalid_hex_wrong_length(self):
        """Test invalid hex codes fall back to black."""
        assert to_rgb("#00") == (0, 0, 0)  # Too short
        assert to_rgb("#0000000") == (0, 0, 0)  # Too long
        assert to_rgb("#") == (0, 0, 0)  # Only hash

    def test_invalid_hex_non_hex_chars(self):
        """Test hex codes with non-hex characters fall back to black."""
        assert to_rgb("#gggggg") == (0, 0, 0)
        assert to_rgb("#zzzzzz") == (0, 0, 0)
        assert to_rgb("#gg0000") == (0, 0, 0)

    def test_unknown_color_name(self):
        """Test unknown color names fall back to black."""
        assert to_rgb("notacolor") == (0, 0, 0)
        assert to_rgb("foobar") == (0, 0, 0)
        assert to_rgb("") == (0, 0, 0)

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        assert to_rgb(" red ") == (255, 0, 0)
        assert to_rgb("  #ffffff  ") == (255, 255, 255)
        assert to_rgb("\tblue\n") == (0, 0, 255)

    def test_hex_without_hash(self):
        """Test hex codes without leading hash fall back to black."""
        assert to_rgb("ffffff") == (0, 0, 0)
        assert to_rgb("ff0000") == (0, 0, 0)


class TestToHex:
    """Test RGB tuple to hex string conversion."""

    def test_white_black_basic(self):
        """Test basic white and black conversions."""
        assert to_hex((255, 255, 255)) == "#ffffff"
        assert to_hex((0, 0, 0)) == "#000000"

    def test_primary_colors(self):
        """Test primary color conversions."""
        assert to_hex((255, 0, 0)) == "#ff0000"
        assert to_hex((0, 255, 0)) == "#00ff00"
        assert to_hex((0, 0, 255)) == "#0000ff"

    def test_mixed_values(self):
        """Test mixed RGB values."""
        assert to_hex((128, 128, 128)) == "#808080"
        assert to_hex((255, 165, 0)) == "#ffa500"
        assert to_hex((100, 150, 200)) == "#6496c8"

    def test_clamping_high_values(self):
        """Test clamping of values greater than 255."""
        assert to_hex((300, 400, 500)) == "#ffffff"
        assert to_hex((256, 256, 256)) == "#ffffff"
        assert to_hex((255, 300, 255)) == "#ffffff"
        assert to_hex((300, 0, 100)) == "#ff0064"

    def test_clamping_negative_values(self):
        """Test clamping of negative values."""
        assert to_hex((-10, -20, -30)) == "#000000"
        assert to_hex((-1, 0, 0)) == "#000000"
        assert to_hex((100, -50, 200)) == "#6400c8"

    def test_clamping_mixed_out_of_bounds(self):
        """Test clamping with mixed values."""
        assert to_hex((300, -10, 100)) == "#ff0064"
        assert to_hex((-50, 128, 300)) == "#0080ff"
        assert to_hex((500, 500, 500)) == "#ffffff"

    def test_floating_point_values(self):
        """Test conversion of floating point values."""
        assert to_hex((255.5, 127.5, 0.0)) == "#ff7f00"
        assert to_hex((100.1, 100.9, 100.5)) == "#646464"

    def test_zero_values(self):
        """Test all zero and all max combinations."""
        assert to_hex((0, 0, 0)) == "#000000"
        assert to_hex((255, 255, 255)) == "#ffffff"

    def test_single_byte_values(self):
        """Test single byte values are zero-padded."""
        assert to_hex((1, 2, 3)) == "#010203"
        assert to_hex((15, 15, 15)) == "#0f0f0f"


class TestLerpColor:
    """Test linear interpolation between colors."""

    def test_endpoints(self):
        """Test interpolation at endpoints (0 and 1)."""
        assert lerp_color("#000000", "#ffffff", 0.0) == "#000000"
        assert lerp_color("#000000", "#ffffff", 1.0) == "#ffffff"

    def test_midpoint(self):
        """Test interpolation at midpoint (0.5)."""
        result = lerp_color("#000000", "#ffffff", 0.5)
        assert result == "#7f7f7f"

    def test_quarter_points(self):
        """Test interpolation at quarter points."""
        result_25 = lerp_color("#000000", "#ffffff", 0.25)
        result_75 = lerp_color("#000000", "#ffffff", 0.75)
        assert result_25 == "#3f3f3f"
        assert result_75 == "#bfbfbf"

    def test_out_of_bounds_clamp_low(self):
        """Test that t < 0 clamps to 0."""
        assert lerp_color("#000000", "#ffffff", -1.0) == "#000000"
        assert lerp_color("#000000", "#ffffff", -0.5) == "#000000"

    def test_out_of_bounds_clamp_high(self):
        """Test that t > 1 clamps to 1."""
        assert lerp_color("#000000", "#ffffff", 2.0) == "#ffffff"
        assert lerp_color("#000000", "#ffffff", 1.5) == "#ffffff"

    def test_color_range_red_blue(self):
        """Test interpolation from red to blue."""
        result = lerp_color("#ff0000", "#0000ff", 0.5)
        # Midpoint: (127, 0, 127) -> #7f007f
        assert result == "#7f007f"

    def test_color_range_different_colors(self):
        """Test interpolation between arbitrary colors."""
        # From orange to green
        result = lerp_color("#ffa500", "#008000", 0.5)
        # R: (255+0)/2=127, G: (165+128)/2=146, B: (0+0)/2=0 -> #7f9200
        assert result == "#7f9200"

    def test_named_colors(self):
        """Test lerp with named colors."""
        result = lerp_color("red", "blue", 0.5)
        assert result == "#7f007f"

    def test_string_conversion_of_t(self):
        """Test that t can be passed as a string number."""
        assert lerp_color("#000000", "#ffffff", "0.5") == "#7f7f7f"
        assert lerp_color("#000000", "#ffffff", "0.0") == "#000000"
        assert lerp_color("#000000", "#ffffff", "1.0") == "#ffffff"


class TestPolarToCartesian:
    """Test polar to Cartesian coordinate conversion."""

    def test_zero_degrees(self):
        """Test 0 degrees should point right (positive X)."""
        x, y = polar_to_cartesian(0, 100)
        assert pytest.approx(x, abs=1e-9) == 100
        assert pytest.approx(y, abs=1e-9) == 0

    def test_90_degrees(self):
        """Test 90 degrees should point up (positive Y)."""
        x, y = polar_to_cartesian(90, 100)
        assert pytest.approx(x, abs=1e-9) == 0
        assert pytest.approx(y, abs=1e-9) == 100

    def test_180_degrees(self):
        """Test 180 degrees should point left (negative X)."""
        x, y = polar_to_cartesian(180, 100)
        assert pytest.approx(x, abs=1e-9) == -100
        assert pytest.approx(y, abs=1e-9) == 0

    def test_270_degrees(self):
        """Test 270 degrees should point down (negative Y)."""
        x, y = polar_to_cartesian(270, 100)
        assert pytest.approx(x, abs=1e-9) == 0
        assert pytest.approx(y, abs=1e-9) == -100

    def test_45_degrees(self):
        """Test 45 degrees (diagonal)."""
        x, y = polar_to_cartesian(45, 100)
        expected = 100 / math.sqrt(2)
        assert pytest.approx(x, abs=1e-9) == expected
        assert pytest.approx(y, abs=1e-9) == expected

    def test_radius_zero(self):
        """Test zero radius results in origin."""
        x, y = polar_to_cartesian(45, 0)
        assert pytest.approx(x, abs=1e-9) == 0
        assert pytest.approx(y, abs=1e-9) == 0

    def test_negative_radius(self):
        """Test negative radius (points in opposite direction)."""
        x, y = polar_to_cartesian(0, -100)
        assert pytest.approx(x, abs=1e-9) == -100
        assert pytest.approx(y, abs=1e-9) == 0

    def test_rotation_offset_0(self):
        """Test rotation offset of 0 degrees (no change)."""
        x1, y1 = polar_to_cartesian(45, 100)
        x2, y2 = polar_to_cartesian(45, 100, rotation=0)
        assert pytest.approx(x1, abs=1e-9) == x2
        assert pytest.approx(y1, abs=1e-9) == y2

    def test_rotation_offset_90(self):
        """Test 90 degree rotation offset."""
        # 0 degrees + 90 rotation = 90 degrees
        x, y = polar_to_cartesian(0, 100, rotation=90)
        assert pytest.approx(x, abs=1e-9) == 0
        assert pytest.approx(y, abs=1e-9) == 100

    def test_rotation_offset_180(self):
        """Test 180 degree rotation offset."""
        # 0 degrees + 180 rotation = 180 degrees
        x, y = polar_to_cartesian(0, 100, rotation=180)
        assert pytest.approx(x, abs=1e-9) == -100
        assert pytest.approx(y, abs=1e-9) == 0

    def test_rotation_offset_negative(self):
        """Test negative rotation offset."""
        # 90 degrees - 90 rotation = 0 degrees
        x, y = polar_to_cartesian(90, 100, rotation=-90)
        assert pytest.approx(x, abs=1e-9) == 100
        assert pytest.approx(y, abs=1e-9) == 0

    def test_rotation_offset_360(self):
        """Test 360 degree rotation (full rotation, no change)."""
        x1, y1 = polar_to_cartesian(45, 100)
        x2, y2 = polar_to_cartesian(45, 100, rotation=360)
        assert pytest.approx(x1, abs=1e-9) == x2
        assert pytest.approx(y1, abs=1e-9) == y2

    def test_floating_point_angles(self):
        """Test floating point angle values."""
        x, y = polar_to_cartesian(45.5, 100)
        assert isinstance(x, float)
        assert isinstance(y, float)

    def test_float_conversion(self):
        """Test that degree and radius are converted to float."""
        x, y = polar_to_cartesian("45", "100")
        assert isinstance(x, float)
        assert isinstance(y, float)
        expected = 100 / math.sqrt(2)
        assert pytest.approx(x, abs=1e-9) == expected


class TestGenerateId:
    """Test ID generation for SVG elements."""

    def test_returns_string(self):
        """Test that generate_id returns a string."""
        result = generate_id()
        assert isinstance(result, str)

    def test_has_prefix(self):
        """Test that ID contains the specified prefix."""
        result = generate_id(prefix="test")
        assert result.startswith("test_")

    def test_default_prefix(self):
        """Test the default prefix."""
        result = generate_id()
        assert result.startswith("id_")

    def test_correct_length(self):
        """Test that the ID has the correct length (prefix + underscore + suffix)."""
        result = generate_id(prefix="x", length=10)
        # Format: "x_" + 10 chars
        assert len(result) == len("x_") + 10

    def test_custom_length(self):
        """Test custom suffix length."""
        result = generate_id(length=5)
        assert len(result) == len("id_") + 5

    def test_length_zero(self):
        """Test with zero suffix length."""
        result = generate_id(prefix="test", length=0)
        assert result == "test_"

    def test_long_prefix(self):
        """Test with a long prefix."""
        result = generate_id(prefix="my_very_long_prefix", length=6)
        assert result.startswith("my_very_long_prefix_")

    def test_uniqueness(self):
        """Test that successive calls generate different IDs."""
        id1 = generate_id()
        id2 = generate_id()
        # Very likely to be different (unless random seed is fixed)
        assert id1 != id2

    def test_suffix_characters_alphanumeric(self):
        """Test that suffix contains only alphanumeric characters."""
        result = generate_id(length=20)
        suffix = result.split("_", 1)[1]  # Get part after prefix_
        assert all(c.isalnum() for c in suffix)


class TestAddOriginIfRootHasDist:
    """Test origin node insertion for trees with root distance."""

    def test_tree_with_zero_distance(self):
        """Test tree with root distance = 0 remains unchanged."""
        tree = ete3.Tree("((A:1,B:1)AB:0,(C:1,D:1)CD:0)root;", format=1)
        result = add_origin_if_root_has_dist(tree)
        assert result == tree
        assert result.dist == 0.0
        assert len(result.get_leaves()) == 4

    def test_tree_without_distance(self):
        """Test tree with no root distance (None)."""
        tree = ete3.Tree("((A:1,B:1)AB:0.5,(C:1,D:1)CD:0.5)root;", format=1)
        result = add_origin_if_root_has_dist(tree)
        assert result.dist == 0.0

    def test_tree_with_positive_distance(self):
        """Test tree with positive root distance gets origin node."""
        tree = ete3.Tree("((A:1,B:1)AB:0.5,(C:1,D:1)CD:0.5)root:1.0;", format=1)
        result = add_origin_if_root_has_dist(tree)
        # Should have created a new root
        assert result.is_root()
        assert result.dist == 0.0
        # The old root should be a child with the old distance
        assert len(result.children) == 1
        child = result.children[0]
        assert pytest.approx(child.dist) == 1.0
        # Should still have 4 leaves
        assert len(result.get_leaves()) == 4

    def test_origin_node_name(self):
        """Test that origin node has the correct default name."""
        tree = ete3.Tree("(A:1,B:1)AB:2.0;", format=1)
        result = add_origin_if_root_has_dist(tree)
        assert result.name == "Origin"

    def test_custom_origin_name(self):
        """Test origin node with custom name."""
        tree = ete3.Tree("(A:1,B:1)AB:2.0;", format=1)
        result = add_origin_if_root_has_dist(tree, origin_name="MRCA")
        assert result.name == "MRCA"

    def test_preserves_tree_structure(self):
        """Test that tree structure is preserved after adding origin."""
        tree = ete3.Tree("((A:1,B:1)AB:0.5,(C:1,D:1)CD:0.5)root:1.5;", format=1)
        original_leaf_names = set(l.name for l in tree.get_leaves())
        result = add_origin_if_root_has_dist(tree)
        result_leaf_names = set(l.name for l in result.get_leaves())
        assert original_leaf_names == result_leaf_names

    def test_very_small_distance(self):
        """Test with very small but non-zero distance."""
        tree = ete3.Tree("(A:1,B:1)AB:0.0001;", format=1)
        result = add_origin_if_root_has_dist(tree)
        # Should create origin node for any positive distance
        assert result.is_root()
        assert len(result.children) == 1

    def test_negative_distance_treated_as_zero(self):
        """Test that negative distances are treated as zero."""
        tree = ete3.Tree("(A:1,B:1)AB;", format=1)
        tree.dist = -1.0
        result = add_origin_if_root_has_dist(tree)
        # Negative should be clamped to 0, so no origin added
        assert result.dist == 0.0
        assert result.name == "AB"  # Original root

    def test_ensures_root_dist_is_zero(self):
        """Test that root distance is always zero after processing."""
        trees = [
            ete3.Tree("(A:1,B:1)AB:0.0;", format=1),
            ete3.Tree("(A:1,B:1)AB:1.0;", format=1),
            ete3.Tree("(A:1,B:1)AB:5.5;", format=1),
        ]
        for tree in trees:
            result = add_origin_if_root_has_dist(tree)
            assert result.is_root()
            assert result.dist == 0.0
