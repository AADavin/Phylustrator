import ete3
import drawsvg as draw
import math
import numpy as np
import copy
import os
from dataclasses import dataclass

# --- Helper Functions ---
def radial_converter(degree, radius, rotation=0):
    """
    Standard Polar -> Cartesian converter.
    In SVG (y is down):
    - 0 deg = 3 o'clock (Right)
    - Positive angles rotate Clockwise
    """
    # Convert entire angle to radians at once
    theta = math.radians(degree + rotation)

    x = radius * math.cos(theta)
    y = radius * math.sin(theta)
    return x, y


@dataclass
class TreeStyle:
    # Canvas
    height: int = 1000
    width: int = 1000
    radius: int = 400
    degrees: int = 360
    rotation: int = -90

    # Visuals
    leaf_size: int = 5
    leaf_color: str = "black"
    branch_size: int = 2
    branch_color: str = "black"
    node_size: int = 2

# --- Base Class ---
class BaseDrawer:
    def __init__(self, tree, style=None):
        self.t = tree
        
        # If no style is provided, use the defaults
        if style is None:
            self.style = TreeStyle()
        else:
            self.style = style
            
        # Shortcuts for cleaner code (optional, but convenient)
        self.d = draw.Drawing(self.style.width, self.style.height, origin='center', displayInline=True)
        self.d.append(draw.Rectangle(-self.style.width/2, -self.style.height/2, self.style.width, self.style.height, fill="white"))
        
        self.total_length_of_tree = 0 

    # Update helper methods to access self.style.rotation, self.style.radius, etc.
    def _draw_leaf(self, n, branch_color_override=None):
        style = self.style # shorthand
        
        de, re = n.coordinates
        de2, re2 = n.eb_coordinates
        
        # Use overridden color if provided, else use style default
        b_color = branch_color_override if branch_color_override else style.branch_color
        
        x, y = radial_converter(de, re, style.rotation)
        xe, ye = radial_converter(de2, re2 - (style.branch_size / 2), style.rotation)
        
        self.d.append(draw.Circle(x, y, style.leaf_size, fill=style.leaf_color))
        self.d.append(draw.Line(xe, ye, x, y, stroke=b_color, stroke_width=style.branch_size, fill='none'))

    def _draw_internal_node(self, n, branch_color_override=None):
        style = self.style
        b_color = branch_color_override if branch_color_override else style.branch_color

        c1, c2 = n.get_children()
        d1, _ = c1.coordinates
        d2, _ = c2.coordinates
        
        mid, mxd = min([d1, d2]), max([d1, d2])
        
        # Handle coordinate calculation...
        if hasattr(n, "radius_dist"):
             current_radius = n.radius_dist
        else:
             current_radius = (self.total_length_of_tree - n.age) * style.radius / self.total_length_of_tree

        x, y = radial_converter((d1+d2)/2, current_radius, style.rotation)

        if not n.is_root():
            self.d.append(draw.ArcLine(0, 0, current_radius, mid + style.rotation - 180, mxd + style.rotation - 180, 
                                       stroke=b_color, stroke_width=style.branch_size, fill="None"))
            
            up_radius = (self.total_length_of_tree - n.up.age) * style.radius / self.total_length_of_tree
            xe, ye = radial_converter((d1+d2)/2, up_radius - (style.branch_size / 2), style.rotation)
            self.d.append(draw.Line(xe, ye, x, y, stroke=b_color, stroke_width=style.branch_size, fill='none'))

        self.d.append(draw.Circle(x, y, style.node_size, fill=b_color))


class TreeDrawer(BaseDrawer):
    """
    Universal Drawer.
    """

    def __init__(self, tree, style=None):
        super().__init__(tree, style)
        self._calculate_coordinates()

    def _calculate_coordinates(self):
        # 1. Distances (The Universal Logic)
        max_dist = 0
        for n in self.t.traverse("preorder"):
            if n.is_root():
                n.add_feature("dist_to_root", 0)
            else:
                n.add_feature("dist_to_root", n.up.dist_to_root + n.dist)

            if n.dist_to_root > max_dist:
                max_dist = n.dist_to_root

        self.total_length_of_tree = max_dist

        # Scaling Factor
        if self.total_length_of_tree > 0:
            sf = self.style.radius / self.total_length_of_tree
        else:
            sf = 0

        # 2. Angles (Standard Uniform Layout)
        leaves = self.t.get_leaves()
        self.arc_leaf = self.style.degrees / len(leaves)

        for index, l in enumerate(leaves):
            l.add_feature("angle", self.arc_leaf * index)

        for n in self.t.traverse("postorder"):
            if n.is_leaf():
                continue
            c1, c2 = n.get_children()
            # Parent angle is the midpoint of children
            n.add_feature("angle", (c1.angle + c2.angle) / 2)

        # 3. Final Coordinate Assignment
        for n in self.t.traverse():
            r = n.dist_to_root * sf
            n.add_feature("coordinates", (n.angle, r))

    def draw(self, branch2color=None):
        """Standard drawing loop."""
        for n in self.t.traverse("postorder"):
            # 1. Resolve Color
            b_color = self.style.branch_color
            if branch2color and n in branch2color:
                b_color = branch2color[n]
                if b_color == "None": continue

            # 2. Draw
            if n.is_leaf():
                self._draw_leaf_final(n, b_color)
            else:
                self._draw_internal_final(n, b_color)

    def _draw_leaf_final(self, n, color):
        x, y = radial_converter(*n.coordinates, self.style.rotation)

        # Branch starts at parent's radius
        p_angle, p_radius = n.up.coordinates

        # Calculate start point
        xe, ye = radial_converter(n.angle, p_radius - (self.style.branch_size / 2), self.style.rotation)

        self.d.append(draw.Circle(x, y, self.style.leaf_size, fill=self.style.leaf_color))
        self.d.append(draw.Line(xe, ye, x, y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

    def _draw_internal_final(self, n, color):
        if n.is_root(): return

        c1, c2 = n.get_children()

        # We need to draw an arc from child 1 to child 2 at the current radius
        # Instead of using draw.ArcLine (which handles angles differently),
        # we calculate the start/end points manually to guarantee alignment.

        start_angle = min(c1.angle, c2.angle)
        end_angle = max(c1.angle, c2.angle)
        _, radius = n.coordinates

        # Get exact coordinates using OUR reliable converter
        sx, sy = radial_converter(start_angle, radius, self.style.rotation)
        ex, ey = radial_converter(end_angle, radius, self.style.rotation)

        # Draw the Arc using SVG Path
        # A rx ry x-axis-rotation large-arc-flag sweep-flag x y
        # sweep-flag=1 means Clockwise (which matches our increasing angle logic)
        p = draw.Path(stroke=color, stroke_width=self.style.branch_size, fill="none")
        p.M(sx, sy)
        p.A(radius, radius, 0, 0, 1, ex, ey)
        self.d.append(p)

        # Draw the Node
        x, y = radial_converter(n.angle, radius, self.style.rotation)
        self.d.append(draw.Circle(x, y, self.style.node_size, fill=color))

        # Radial line to parent
        p_angle, p_radius = n.up.coordinates
        xe, ye = radial_converter(n.angle, p_radius - (self.style.branch_size / 2), self.style.rotation)
        self.d.append(draw.Line(xe, ye, x, y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

    def highlight_clade(self, node, color="red", opacity=0.3):
        if node.is_leaf(): return
        leaves = node.get_leaves()
        angles = [l.angle for l in leaves]
        min_angle, max_angle = min(angles), max(angles)

        # Add padding
        angle_pad = self.arc_leaf / 2

        # Calculate start/end angles in our rotation space
        # Note: We don't use -180 anymore. We trust radial_converter logic.
        start_deg = min_angle - angle_pad
        end_deg = max_angle + angle_pad

        _, node_radius = node.coordinates
        max_radius = self.style.radius

        # Calculate coordinates for the 4 corners of the wedge
        s_inner_x, s_inner_y = radial_converter(start_deg, node_radius, self.style.rotation)
        e_inner_x, e_inner_y = radial_converter(end_deg, node_radius, self.style.rotation)
        s_outer_x, s_outer_y = radial_converter(start_deg, max_radius, self.style.rotation)
        e_outer_x, e_outer_y = radial_converter(end_deg, max_radius, self.style.rotation)

        # Build the shape manually to guarantee alignment
        p = draw.Path(fill=color, fill_opacity=opacity, stroke="none")
        p.M(s_outer_x, s_outer_y)
        p.A(max_radius, max_radius, 0, 0, 1, e_outer_x, e_outer_y)  # Outer arc
        p.L(e_inner_x, e_inner_y)  # Line in
        p.A(node_radius, node_radius, 0, 0, 0, s_inner_x, s_inner_y)  # Inner arc (sweep=0 for reverse)
        p.Z()  # Close

        self.d.append(p)

    def add_leaf_names(self, mapping=None, text_size=12, padding=10, color="black"):
        """
        Adds text labels using atan2 for correct screen orientation.
        """
        for l in self.t:
            name = l.name
            if mapping and l.name in mapping:
                name = mapping[l.name]
            elif mapping is not None:
                continue

            de, re = l.coordinates
            x, y = radial_converter(de, re, self.style.rotation)

            screen_angle = math.degrees(math.atan2(y, x))

            if -90 <= screen_angle <= 90:
                anchor = 'start'
                rotation = screen_angle
                x_adj, y_adj = radial_converter(de, re + padding, self.style.rotation)
            else:
                anchor = 'end'
                rotation = screen_angle - 180
                x_adj, y_adj = radial_converter(de, re + padding, self.style.rotation)

            self.d.append(draw.Text(name, text_size, x_adj, y_adj, text_anchor=anchor, fill=color,
                                    transform=f"rotate({rotation}, {x_adj}, {y_adj})"))