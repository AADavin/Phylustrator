import ete3
import drawsvg as draw
import math
import numpy as np
import copy
import os
from dataclasses import dataclass
import random  

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

    def add_scale_bar(self, length=None, label=None, x=None, y=None, color="black", width=2, font_size=12):
        """
        Adds a scale bar to the plot.

        :param length: Length in tree units (e.g., 0.1 substitutions).
                       If None, auto-calculates a round number.
        :param label: Text label (e.g. "0.1 subst/site"). Auto-generated if None.
        :param x, y: Position (defaults to bottom-left).
        """
        # 1. Determine Length (Auto-calc if missing)
        if length is None:
            # Try to find a nice round number (e.g. 0.1, 0.05, 1.0)
            # Rough logic: 10% of total tree length
            target = self.total_length_of_tree * 0.1
            if target == 0: target = 1

            # Round to nearest 1 significant digit
            import math
            exponent = math.floor(math.log10(target))
            length = round(target, -exponent)

        # 2. Calculate Pixel Length
        px_length = length * self.sf

        # 3. Text Label
        if label is None:
            label = f"{length}"

        # 4. Position (Default: Bottom-Left)
        if x is None:
            x = -self.style.width / 2 + 50
        if y is None:
            y = self.style.height / 2 - 50  # Bottom for SVG (y increases downwards)

        # 5. Draw
        # Line
        self.d.append(draw.Line(x, y, x + px_length, y, stroke=color, stroke_width=width))

        # Ticks (Vertical ends)
        tick_h = 5
        self.d.append(draw.Line(x, y - tick_h, x, y + tick_h, stroke=color, stroke_width=width))
        self.d.append(draw.Line(x + px_length, y - tick_h, x + px_length, y + tick_h, stroke=color, stroke_width=width))

        # Label (Centered below line)
        self.d.append(draw.Text(label, font_size, x + (px_length / 2), y + 20, fill=color, text_anchor="middle"))

    def save_figure(self, filename):
        """
        Saves the current drawing to a file.
        Supports .svg, .png, and .pdf depending on drawsvg backend.
        """
        if filename.endswith(".svg"):
            self.d.save_svg(filename)
        elif filename.endswith(".png"):
            self.d.save_png(filename)
        elif filename.endswith(".pdf"):
            # Requires cairo
            self.d.save_pdf(filename)
        else:
            # Default to SVG if unknown
            self.d.save_svg(filename + ".svg")
        print(f"Figure saved to {filename}")


class RadialTreeDrawer(BaseDrawer):
    """
    Universal Drawer.
    """

    def __init__(self, tree, style=None):
        super().__init__(tree, style)
        self._calculate_coordinates()

    def _calculate_coordinates(self):
        # 1. Calculate Distances (Time)
        max_dist = 0

        for n in self.t.traverse("preorder"):
            if n.is_root():
                # FIX: Initialize with the Stem Length (offset), not 0
                # defaults to 0 if not set
                start_dist = getattr(n, "dist", 0.0)
                n.add_feature("dist_to_root", start_dist)
            else:
                n.add_feature("dist_to_root", n.up.dist_to_root + n.dist)

            if n.dist_to_root > max_dist: max_dist = n.dist_to_root
                max_dist = n.dist_to_root

        self.total_length_of_tree = max_dist

        # Scaling Factor
        if self.total_length_of_tree > 0:
            self.sf = self.style.radius / self.total_length_of_tree
        else:
            self.sf = 0

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
            r = n.dist_to_root * self.sf
            n.add_feature("coordinates", (n.angle, r))

    def draw(self, branch2color=None, hide_radial_lines=None):
        """
        Standard drawing loop.
        :param hide_radial_lines: List of nodes where the radial (vertical) connection
                                  to the parent should be skipped.
        """
        hidden_set = set(hide_radial_lines) if hide_radial_lines else set()

        for n in self.t.traverse("postorder"):
            # 1. Resolve Color
            b_color = self.style.branch_color
            if branch2color and n in branch2color:
                b_color = branch2color[n]
                if b_color == "None": continue

            # 2. Draw
            if n.is_leaf():
                self._draw_leaf_final(n, b_color, hide_line=(n in hidden_set))
            else:
                self._draw_internal_final(n, b_color, hide_line=(n in hidden_set))

    def _draw_leaf_final(self, n, color, hide_line=False):
        x, y = radial_converter(*n.coordinates, self.style.rotation)
        self.d.append(draw.Circle(x, y, self.style.leaf_size, fill=self.style.leaf_color))

        if not hide_line:
            p_angle, p_radius = n.up.coordinates
            xe, ye = radial_converter(n.angle, p_radius - (self.style.branch_size / 2), self.style.rotation)
            self.d.append(draw.Line(xe, ye, x, y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

    def _draw_internal_final(self, n, color, hide_line=False):
        if n.is_root(): return

        c1, c2 = n.get_children()

        # 1. Always Draw Arc (Shoulder) using Node's Color
        start_angle = min(c1.angle, c2.angle)
        end_angle = max(c1.angle, c2.angle)
        _, radius = n.coordinates

        sx, sy = radial_converter(start_angle, radius, self.style.rotation)
        ex, ey = radial_converter(end_angle, radius, self.style.rotation)

        p = draw.Path(stroke=color, stroke_width=self.style.branch_size, fill="none")
        p.M(sx, sy)
        p.A(radius, radius, 0, 0, 1, ex, ey)
        self.d.append(p)

        # 2. Always Draw Node Circle
        x, y = radial_converter(n.angle, radius, self.style.rotation)
        self.d.append(draw.Circle(x, y, self.style.node_size, fill=color))

        # 3. Draw Radial Line (Only if not hidden)
        if not hide_line:
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

    # --- DECORATION METHODS ---

    def gradient_branch(self, node, colors=("red", "blue"), size=None, opacity=1.0):
        """
        Draws ONLY the gradient line for the branch leading to the node.
        Does not draw nodes or arcs.
        """
        if node.is_root(): return

        s_width = size if size else self.style.branch_size

        # Coordinates
        x_end, y_end = radial_converter(*node.coordinates, self.style.rotation)
        p_angle, p_radius = node.up.coordinates
        x_start, y_start = radial_converter(node.angle, p_radius - (self.style.branch_size / 2), self.style.rotation)

        # Create Gradient
        grad_id = f"grad_{node.name}_{random.randint(0, 99999)}"
        gradient = draw.LinearGradient(x_start, y_start, x_end, y_end, id=grad_id)
        gradient.add_stop(0, colors[0], 1)
        gradient.add_stop(1, colors[1], 1)

        self.d.append(draw.Line(x_start, y_start, x_end, y_end,
                                stroke=gradient, stroke_width=s_width, stroke_opacity=opacity, fill='none'))

    def highlight_branch(self, node, color="red", size=None, opacity=1.0, include_arc=False):
        """
        Overlays a colored line on the branch.
        :param include_arc: If True, also colors the horizontal 'shoulder' arc if this is an internal node.
        """
        if node.is_root(): return
        s_width = size if size else self.style.branch_size

        # 1. Radial Line (Vertical)
        x, y = radial_converter(*node.coordinates, self.style.rotation)
        p_angle, p_radius = node.up.coordinates
        xe, ye = radial_converter(node.angle, p_radius - (self.style.branch_size / 2), self.style.rotation)

        self.d.append(draw.Line(xe, ye, x, y, stroke=color, stroke_width=s_width, stroke_opacity=opacity, fill='none'))

        # 2. Horizontal Arc (Shoulder) - Optional
        if include_arc and not node.is_leaf():
            c1, c2 = node.get_children()
            start_angle = min(c1.angle, c2.angle)
            end_angle = max(c1.angle, c2.angle)
            _, radius = node.coordinates

            # Recalculate Arc points
            sx, sy = radial_converter(start_angle, radius, self.style.rotation)
            ex, ey = radial_converter(end_angle, radius, self.style.rotation)

            p = draw.Path(stroke=color, stroke_width=s_width, stroke_opacity=opacity, fill="none")
            p.M(sx, sy)
            p.A(radius, radius, 0, 0, 1, ex, ey)
            self.d.append(p)



    def add_node_shapes(self, mapping, size=None, stroke="black", stroke_width=1):
        """
        Adds circles to specific nodes.
        :param mapping: Dictionary {node_object: color_string} or {node_name: color_string}
        """
        r = size if size else self.style.node_size * 2

        for n in self.t.traverse():
            # Check if node or node name is in mapping
            if n in mapping:
                color = mapping[n]
            elif n.name in mapping:
                color = mapping[n.name]
            else:
                continue

            x, y = radial_converter(*n.coordinates, self.style.rotation)
            self.d.append(draw.Circle(x, y, r, fill=color, stroke=stroke, stroke_width=stroke_width))

    def add_transfer_links(self, transfers, color="orange", gradient_colors=None, min_freq=0.0, opacity_scale=1.0,
                           curve_factor=0.5):
        import random
        name_to_node = {n.name: n for n in self.t.traverse()}

        # Pre-calculate node distances from root (Simulated Time) for fast lookup
        # We assume n.dist_to_root was calculated in _calculate_coordinates
        # If not, we can assume n.dist adds up.

        for tr in transfers:
            freq = tr['freq']
            if freq < min_freq: continue

            node_from = name_to_node.get(str(tr['from']))
            node_to = name_to_node.get(str(tr['to']))

            if not node_from or not node_to: continue

            # --- CALCULATE START RADIUS (Time-aware) ---
            f_angle, f_rad_child = node_from.coordinates

            # Default to midpoint if no time provided
            start_radius = f_rad_child  # Placeholder

            if 'time' in tr and not node_from.is_root():
                # We need to map Zombi Time -> Radial Coordinates
                # 1. Get Parent Radius (Time Start of Branch)
                _, f_rad_parent = node_from.up.coordinates

                # 2. Get Tree Distance (Time End of Branch)
                # n.dist_to_root should be available.
                # Note: We must ensure Zombi Time units match Tree Dist units.
                # Usually Zombi CompleteTree.nwk branch lengths = Time.

                dist_parent = node_from.up.dist_to_root
                dist_child = node_from.dist_to_root

                # 3. Interpolate
                # If Zombi time is absolute (from root = 0)
                event_time = tr['time']

                # Sanity check: is event_time inside the branch interval?
                # Sometimes numerical float errors happen, so we clamp.
                if dist_child > dist_parent:
                    fraction = (event_time - dist_parent) / (dist_child - dist_parent)
                    fraction = max(0.0, min(1.0, fraction))  # Clamp 0-1

                    # Map to visual radius
                    start_radius = f_rad_parent + fraction * (f_rad_child - f_rad_parent)
                else:
                    # Zero length branch or root
                    start_radius = f_rad_child
            else:
                # Fallback to Midpoint
                if node_from.is_root():
                    start_radius = f_rad_child
                else:
                    _, p_rad = node_from.up.coordinates
                    start_radius = (f_rad_child + p_rad) / 2

            sx, sy = radial_converter(f_angle, start_radius, self.style.rotation)

            # --- CALCULATE END RADIUS (Target) ---
            # Ideally, we should also know the ARRIVAL time.
            # In 'LT' (Leaving Transfer), the arrival is usually instantaneous in Zombi.
            # So we use the SAME time for the destination branch.

            t_angle, t_rad_child = node_to.coordinates

            if 'time' in tr and not node_to.is_root():
                _, t_rad_parent = node_to.up.coordinates
                dist_parent = node_to.up.dist_to_root
                dist_child = node_to.dist_to_root
                event_time = tr['time']

                if dist_child > dist_parent:
                    fraction = (event_time - dist_parent) / (dist_child - dist_parent)
                    fraction = max(0.0, min(1.0, fraction))
                    end_radius = t_rad_parent + fraction * (t_rad_child - t_rad_parent)
                else:
                    end_radius = t_rad_child
            else:
                if node_to.is_root():
                    end_radius = t_rad_child
                else:
                    _, p_rad = node_to.up.coordinates
                    end_radius = (t_rad_child + p_rad) / 2

            ex, ey = radial_converter(t_angle, end_radius, self.style.rotation)

            # --- DRAW (Same as before) ---
            if gradient_colors:
                grad_id = f"tr_grad_{random.randint(0, 9999999)}"
                stroke_paint = draw.LinearGradient(sx, sy, ex, ey, id=grad_id)
                stroke_paint.add_stop(0, gradient_colors[0], 1)
                stroke_paint.add_stop(1, gradient_colors[1], 1)
            else:
                stroke_paint = color

            cx1 = sx * (1 - curve_factor)
            cy1 = sy * (1 - curve_factor)
            cx2 = ex * (1 - curve_factor)
            cy2 = ey * (1 - curve_factor)

            alpha = min(1.0, freq * opacity_scale)

            p = draw.Path(stroke=stroke_paint, stroke_width=self.style.branch_size,
                          stroke_opacity=alpha, fill="none")
            p.M(sx, sy)
            p.C(cx1, cy1, cx2, cy2, ex, ey)
            self.d.append(p)

    def mark_events(self, events, type_filter="D", color="red", shape="circle", size=3):
        """
        Draws symbols on the branches at the exact event times.

        :param events: List of dicts [{'time': 1.2, 'type': 'D', 'node': 'n1'}, ...]
        :param type_filter: "D", "L", etc.
        """
        name_to_node = {n.name: n for n in self.t.traverse()}

        for ev in events:
            if ev.get('type') != type_filter: continue

            node_name = str(ev['node'])
            node = name_to_node.get(node_name)
            if not node or node.is_root(): continue

            # Interpolate Position
            # 1. Get Interval
            _, rad_parent = node.up.coordinates
            dist_parent = node.up.dist_to_root

            _, rad_child = node.coordinates
            dist_child = node.dist_to_root

            # 2. Calculate Radius
            event_time = ev['time']
            if dist_child > dist_parent:
                fraction = (event_time - dist_parent) / (dist_child - dist_parent)
                fraction = max(0.0, min(1.0, fraction))

                final_radius = rad_parent + fraction * (rad_child - rad_parent)
            else:
                final_radius = rad_child

            # 3. Draw
            x, y = radial_converter(node.angle, final_radius, self.style.rotation)

            if shape == "circle":
                self.d.append(draw.Circle(x, y, size, fill=color))
            elif shape == "x":
                # Draw a small X (e.g. for Losses)
                self.d.append(draw.Line(x - size, y - size, x + size, y + size, stroke=color, stroke_width=1))
                self.d.append(draw.Line(x + size, y - size, x - size, y + size, stroke=color, stroke_width=1))

    def add_leaf_shapes(self, mapping, size=None, padding=10, stroke="black", stroke_width=1):
        """
        Adds circles next to the tips (e.g., for showing presence/absence).
        :param mapping: Dictionary {leaf_name: color_string}
        """
        r = size if size else self.style.leaf_size

        for l in self.t.get_leaves():
            if l.name not in mapping: continue

            color = mapping[l.name]
            angle, radius = l.coordinates

            # Position is radius + padding
            x, y = radial_converter(angle, radius + padding, self.style.rotation)

            self.d.append(draw.Circle(x, y, r, fill=color, stroke=stroke, stroke_width=stroke_width))

    def add_ring(self, mapping, width=20, padding=10, stroke="none", opacity=1.0):
        """
        Adds a heatmap-style ring outside the tree.
        :param mapping: Dictionary {leaf_name: color_string}
        """
        # Inner and Outer radius of the ring
        r_inner = self.style.radius + padding
        r_outer = r_inner + width

        # Iterate over all leaves to ensure the ring is continuous (or has gaps where data is missing)
        for l in self.t.get_leaves():
            if l.name not in mapping: continue

            color = mapping[l.name]

            # Calculate the angular wedge for this leaf
            # Start = angle - half_arc, End = angle + half_arc
            start_deg = l.angle - (self.arc_leaf / 2)
            end_deg = l.angle + (self.arc_leaf / 2)

            # Calculate 4 corners of the wedge segment
            sx_in, sy_in = radial_converter(start_deg, r_inner, self.style.rotation)
            ex_in, ey_in = radial_converter(end_deg, r_inner, self.style.rotation)
            sx_out, sy_out = radial_converter(start_deg, r_outer, self.style.rotation)
            ex_out, ey_out = radial_converter(end_deg, r_outer, self.style.rotation)

            # Draw Segment
            p = draw.Path(fill=color, fill_opacity=opacity, stroke=stroke)
            p.M(sx_out, sy_out)
            p.A(r_outer, r_outer, 0, 0, 1, ex_out, ey_out)  # Outer Arc
            p.L(ex_in, ey_in)  # Line In
            p.A(r_inner, r_inner, 0, 0, 0, sx_in, sy_in)  # Inner Arc (Reverse)
            p.Z()
            self.d.append(p)

    def add_legend(self, title, mapping, position="top-left", symbol="circle", text_size=12, padding=20):
        """
        Adds a legend to the canvas.

        :param title: Title string for the legend.
        :param mapping: Dictionary {Label: Color} to display.
        :param position: "top-left", "top-right", "bottom-left", "bottom-right",
                         or a tuple (x, y) for custom coordinates.
        :param symbol: "circle", "square", or "line".
        """
        # 1. Determine Start Coordinates
        # (0,0) is center. Top-Left is (-w/2, -h/2).
        w, h = self.style.width, self.style.height

        if position == "top-left":
            x = -w / 2 + padding
            y = -h / 2 + padding
        elif position == "top-right":
            x = w / 2 - padding - 150  # Approximate width of legend
            y = -h / 2 + padding
        elif position == "bottom-left":
            x = -w / 2 + padding
            y = h / 2 - padding - (len(mapping) * text_size * 1.5)
        elif position == "bottom-right":
            x = w / 2 - padding - 150
            y = h / 2 - padding - (len(mapping) * text_size * 1.5)
        elif isinstance(position, tuple):
            x, y = position
        else:
            x, y = -w / 2 + padding, -h / 2 + padding

        # 2. Draw Group (Optional container, currently just drawing directly)

        # Draw Title
        self.d.append(draw.Text(title, text_size + 2, x, y + text_size, font_weight="bold", fill="black"))
        y += (text_size * 2)  # Space after title

        # Draw Items
        for label, color in mapping.items():
            # Draw Symbol
            if symbol == "circle":
                self.d.append(draw.Circle(x + 5, y - 4, 5, fill=color, stroke="black", stroke_width=0.5))
            elif symbol == "square":
                self.d.append(draw.Rectangle(x, y - 8, 10, 10, fill=color, stroke="black", stroke_width=0.5))
            elif symbol == "line":
                self.d.append(draw.Line(x, y - 3, x + 15, y - 3, stroke=color, stroke_width=2))

            # Draw Label
            self.d.append(draw.Text(label, text_size, x + 20, y, fill="black"))

            # Move Down
            y += (text_size * 1.5)

    def add_text(self, text, x=None, y=None, node=None, radius_offset=0, size=12, color="black", rotation=0,
                 anchor="middle", font_weight="normal"):
        """
        Adds text to the canvas.

        Usage 1 (Manual): provide x and y.
            drawer.add_text("Figure A", x=-400, y=-400)

        Usage 2 (Smart): provide a node.
            drawer.add_text("Key Event", node=my_node, radius_offset=20)
        """
        # Case 1: Snap to Node
        if node:
            angle, radius = node.coordinates
            # Apply offset (e.g. to put text slightly above/outside the node)
            calc_x, calc_y = radial_converter(angle, radius + radius_offset, self.style.rotation)

            # If user didn't override x/y, use calculated
            final_x = x if x is not None else calc_x
            final_y = y if y is not None else calc_y

        # Case 2: Manual Coordinates
        else:
            final_x = x if x is not None else 0
            final_y = y if y is not None else 0

        self.d.append(draw.Text(text, size, final_x, final_y,
                                text_anchor=anchor,
                                font_weight=font_weight,
                                fill=color,
                                transform=f"rotate({rotation}, {final_x}, {final_y})"))

    def add_heatmap_matrix(self, matrix, columns=None, start_radius=None, ring_width=20, gap=2, cmap=None,
                               border="none", opacity=1.0):
        """
        Draws multiple concentric rings based on a matrix of values.

        :param matrix: Dictionary {leaf_name: {col_name: value}} OR Pandas DataFrame.
        :param columns: List of column names to plot (defines order). If None, uses all keys.
        :param start_radius: Radius to start the first ring. Defaults to style.radius + 10.
        :param ring_width: Width of each individual ring.
        :param gap: Gap between rings.
        :param cmap: Dictionary {value: color} or function(value) -> color.
        """
        # 1. Handle Input Formats
        # If pandas DataFrame, convert to dict
        if hasattr(matrix, "to_dict"):
            # orient='index' gives {row_label: {col_label: value}}
            matrix = matrix.to_dict(orient='index')
            if columns is None:
                # Get columns from the first row keys
                first_key = next(iter(matrix))
                columns = list(matrix[first_key].keys())

        if columns is None:
            # Fallback for raw dict: collect all unique keys from all rows
            all_keys = set()
            for row in matrix.values():
                all_keys.update(row.keys())
            columns = sorted(list(all_keys))

        # 2. Determine Start Radius
        current_radius = start_radius if start_radius else (self.style.radius + 10)

        # 3. Draw Rings Loop
        for col in columns:
            # Create a simple mapping for just this column: {leaf: color}
            col_mapping = {}

            for leaf in self.t.get_leaves():
                if leaf.name in matrix:
                    val = matrix[leaf.name].get(col, None)

                    # Resolve Color
                    if val is None:
                        continue  # Skip missing data

                    if isinstance(cmap, dict):
                        color = cmap.get(val, "grey")
                    elif callable(cmap):
                        color = cmap(val)
                    else:
                        color = str(val)  # Assume value IS the color string

                    col_mapping[leaf.name] = color

            # Draw the single ring using our existing low-level function
            # We temporarily override style.radius to place the ring correctly
            # (This is a bit of a hack, but efficient. A cleaner way is to update add_ring to take explicit radius)

            # Better approach: Update add_ring to accept an explicit 'radius_override'
            # OR just calculate the geometry here. Let's rely on add_ring but we need to modify it slightly
            # to allow arbitrary start radii, OR just write the geometry here.

            # Let's write the geometry here to keep add_ring simple.
            self._draw_matrix_ring(col_mapping, current_radius, ring_width, border, opacity)

            # Step outward
            current_radius += (ring_width + gap)

    def _draw_matrix_ring(self, mapping, r_inner, width, stroke, opacity):
        """Helper to draw a specific ring at a specific radius."""
        r_outer = r_inner + width

        for l in self.t.get_leaves():
            if l.name not in mapping: continue

            color = mapping[l.name]

            # Calculate angles (same logic as add_ring)
            start_deg = l.angle - (self.arc_leaf / 2)
            end_deg = l.angle + (self.arc_leaf / 2)

            sx_in, sy_in = radial_converter(start_deg, r_inner, self.style.rotation)
            ex_in, ey_in = radial_converter(end_deg, r_inner, self.style.rotation)
            sx_out, sy_out = radial_converter(start_deg, r_outer, self.style.rotation)
            ex_out, ey_out = radial_converter(end_deg, r_outer, self.style.rotation)

            p = draw.Path(fill=color, fill_opacity=opacity, stroke=stroke)
            p.M(sx_out, sy_out)
            p.A(r_outer, r_outer, 0, 0, 1, ex_out, ey_out)
            p.L(ex_in, ey_in)
            p.A(r_inner, r_inner, 0, 0, 0, sx_in, sy_in)
            p.Z()
            self.d.append(p)


class VerticalTreeDrawer(BaseDrawer):
    """
    Rectangular (Linear) Tree Drawer.
    """

    def __init__(self, tree, style=None):
        super().__init__(tree, style)
        self._calculate_coordinates()

    def _calculate_coordinates(self):
        # 1. Calculate Distances (Time)
        max_dist = 0

        for n in self.t.traverse("preorder"):
            if n.is_root():
                # FIX: Initialize with the Stem Length (offset), not 0
                # defaults to 0 if not set
                start_dist = getattr(n, "dist", 0.0)
                n.add_feature("dist_to_root", start_dist)
            else:
                n.add_feature("dist_to_root", n.up.dist_to_root + n.dist)

            if n.dist_to_root > max_dist: max_dist = n.dist_to_root

        self.total_length_of_tree = max_dist

        # Scaling: Map [0, max_dist] -> [Start_Pixel, End_Pixel]
        # We leave 150px padding for labels
        available_width = self.style.width - 150
        self.sf = available_width / max_dist if max_dist > 0 else 0

        # Define the Zero-Point (Root X)
        self.root_x = -self.style.width / 2 + 50

        # 2. Assign Node Coordinates
        # Y-axis logic (Spreading leaves evenly)
        leaves = self.t.get_leaves()
        available_height = self.style.height - 100
        sf_y = available_height / len(leaves)
        start_y = -self.style.height / 2 + 50

        for i, l in enumerate(leaves):
            l.add_feature("y_coord", start_y + (i * sf_y))

        for n in self.t.traverse("postorder"):
            if n.is_leaf(): continue
            children = n.get_children()
            mean_y = sum([c.y_coord for c in children]) / len(children)
            n.add_feature("y_coord", mean_y)

        # Final Assignment
        for n in self.t.traverse():
            # Calculate X using the GLOBAL scaler
            x = self.root_x + (n.dist_to_root * self.sf)
            n.add_feature("coordinates", (x, n.y_coord))

    def time_to_x(self, time):
        """Helper to convert absolute time to X pixel position."""
        return self.root_x + (time * self.sf)

    def add_transfer_links(self, transfers, color="orange", gradient_colors=None, min_freq=0.0, opacity_scale=1.0,
                           curve_factor=0.5):
        """
        Draws strictly vertical transfer lines based on exact time.
        """
        import random
        name_to_node = {n.name: n for n in self.t.traverse()}

        for tr in transfers:
            freq = tr['freq']
            if freq < min_freq: continue

            node_from = name_to_node.get(str(tr['from']))
            node_to = name_to_node.get(str(tr['to']))

            if not node_from or not node_to: continue

            # --- 1. DETERMINE X (Strictly Vertical) ---
            if 'time' in tr:
                # Use Global Time Axis
                event_x = self.time_to_x(tr['time'])

                # Sanity Check: Clamp to branch bounds if slight mismatch
                # (Optional: keeps lines from floating in empty space if time > branch tip)
                # But generally, trust the Global Time.
                start_x = event_x
                end_x = event_x
            else:
                # Fallback: Midpoint (Only if time is missing)
                fx, _ = node_from.coordinates
                tx, _ = node_to.coordinates
                start_x = fx
                end_x = tx
                # Note: This fallback WILL produce slanted lines if fx != tx
                # But Zombi data should always have 'time'.

            # --- 2. DETERMINE Y (Topology) ---
            _, start_y = node_from.coordinates  # Height of donor branch
            _, end_y = node_to.coordinates  # Height of recipient branch

            # --- 3. DRAW ---
            # Standard Bezier logic, but now Start_X == End_X
            if gradient_colors:
                grad_id = f"tr_v_{random.randint(0, 9999999)}"
                stroke_paint = draw.LinearGradient(start_x, start_y, end_x, end_y, id=grad_id)
                stroke_paint.add_stop(0, gradient_colors[0], 1)
                stroke_paint.add_stop(1, gradient_colors[1], 1)
            else:
                stroke_paint = color

            alpha = min(1.0, freq * opacity_scale)

            # Control Points for Sigmoid (Vertical)
            # We pull the curve vertically to make it look like a smooth "jump"
            dist_y = end_y - start_y
            cx1 = start_x + (dist_y * 0.1)  # Tiny horizontal nudge? No, keep it vertical.
            # actually, for vertical sankey, control points should be:
            # (start_x, start_y + offset) and (end_x, end_y - offset)

            cx1 = start_x
            cy1 = start_y + (dist_y * curve_factor)
            cx2 = end_x
            cy2 = end_y - (dist_y * curve_factor)

            p = draw.Path(stroke=stroke_paint, stroke_width=self.style.branch_size,
                          stroke_opacity=alpha, fill="none")
            p.M(start_x, start_y)
            p.C(cx1, cy1, cx2, cy2, end_x, end_y)
            self.d.append(p)

    def draw(self, branch2color=None, hide_radial_lines=None):
        hidden_set = set(hide_radial_lines) if hide_radial_lines else set()

        for n in self.t.traverse("postorder"):
            b_color = self.style.branch_color
            if branch2color and n in branch2color:
                b_color = branch2color[n]
                if b_color == "None": continue

            if n.is_leaf():
                self._draw_leaf_final(n, b_color, hide_line=(n in hidden_set))
            else:
                self._draw_internal_final(n, b_color, hide_line=(n in hidden_set))

    def _draw_leaf_final(self, n, color, hide_line=False):
        x, y = n.coordinates
        self.d.append(draw.Circle(x, y, self.style.leaf_size, fill=self.style.leaf_color))

        if not hide_line and not n.is_root():
            p_x, p_y = n.up.coordinates
            self.d.append(draw.Line(p_x, y, x, y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

    def _draw_internal_final(self, n, color, hide_line=False):
        # FIX: Do NOT return if root. We still need to draw the vertical bar for children!
        # if n.is_root(): return  <-- DELETED

        x, y = n.coordinates
        c1, c2 = n.get_children()

        # 1. Vertical Line (The "Split" bar)
        min_y = min([c.y_coord for c in n.get_children()])
        max_y = max([c.y_coord for c in n.get_children()])

        self.d.append(draw.Line(x, min_y, x, max_y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

        # 2. Node Circle
        self.d.append(draw.Circle(x, y, self.style.node_size, fill=color))

        # 3. Horizontal Line to Parent (Only if NOT root)
        if not n.is_root() and not hide_line:
            p_x, p_y = n.up.coordinates
            self.d.append(draw.Line(p_x, y, x, y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

    

    def highlight_branch(self, node, color="red", size=None, opacity=1.0, include_arc=False):
        if node.is_root(): return
        s_width = size if size else self.style.branch_size
        x, y = node.coordinates
        p_x, p_y = node.up.coordinates
        self.d.append(draw.Line(p_x, y, x, y, stroke=color, stroke_width=s_width, stroke_opacity=opacity))
        if include_arc and not node.is_leaf():
            min_y = min([c.y_coord for c in node.get_children()])
            max_y = max([c.y_coord for c in node.get_children()])
            self.d.append(draw.Line(x, min_y, x, max_y, stroke=color, stroke_width=s_width, stroke_opacity=opacity))

    def gradient_branch(self, node, colors=("red", "blue"), size=None, opacity=1.0):
        if node.is_root(): return
        s_width = size if size else self.style.branch_size
        x, y = node.coordinates
        p_x, _ = node.up.coordinates
        grad_id = f"grad_lin_{node.name}_{random.randint(0, 99999)}"
        gradient = draw.LinearGradient(p_x, y, x, y, id=grad_id)
        gradient.add_stop(0, colors[0], 1)
        gradient.add_stop(1, colors[1], 1)
        self.d.append(draw.Line(p_x, y, x, y, stroke=gradient, stroke_width=s_width, stroke_opacity=opacity))

    def add_leaf_names(self, mapping=None, text_size=12, padding=10, color="black"):
        for l in self.t.get_leaves():
            name = l.name
            if mapping and l.name in mapping:
                name = mapping[l.name]
            elif mapping is not None:
                continue
            x, y = l.coordinates
            self.d.append(draw.Text(name, text_size, x + padding, y + (text_size / 3), fill=color, text_anchor="start"))

    def add_text(self, text, x=None, y=None, node=None, offset_x=0, offset_y=0, size=12, color="black",
                 anchor="middle"):
        if node:
            nx, ny = node.coordinates
            final_x, final_y = nx + offset_x, ny + offset_y
        else:
            final_x, final_y = (x if x else 0), (y if y else 0)
        self.d.append(draw.Text(text, size, final_x, final_y, fill=color, text_anchor=anchor))

    def add_heatmap_matrix(self, matrix, columns=None, start_x=None, box_width=20, gap=2, cmap=None, border="none",
                           opacity=1.0):
        """
        Draws columns of heatmap boxes to the right of the tree.

        :param start_x: X-coordinate to start the first column.
                        Defaults to (max_x_of_tree + 10).
        """
        # 1. Handle Input Formats (Same as Radial)
        if hasattr(matrix, "to_dict"):
            matrix = matrix.to_dict(orient='index')
            if columns is None:
                first_key = next(iter(matrix))
                columns = list(matrix[first_key].keys())

        if columns is None:
            all_keys = set()
            for row in matrix.values():
                all_keys.update(row.keys())
            columns = sorted(list(all_keys))

        # 2. Determine Start X
        # Find the furthest tip to know where the tree ends
        max_tree_x = max([l.coordinates[0] for l in self.t.get_leaves()])
        current_x = start_x if start_x else (max_tree_x + 10)

        # 3. Draw Columns
        for col in columns:
            # We iterate leaves to keep order consistent with tree topology
            for l in self.t.get_leaves():
                if l.name not in matrix: continue

                val = matrix[l.name].get(col, None)
                if val is None: continue

                # Resolve Color
                if isinstance(cmap, dict):
                    color = cmap.get(val, "grey")
                elif callable(cmap):
                    color = cmap(val)
                else:
                    color = str(val)

                # Geometry
                # Leaf coordinates are (x, y). We use 'current_x' for the box X, and leaf 'y' for box Y.
                # Center the box on the leaf's Y.
                lx, ly = l.coordinates

                # Draw Rectangle
                # x, y, width, height. y is top-left, so we do ly - (box_width/2)
                self.d.append(draw.Rectangle(
                    current_x,
                    ly - (box_width / 2),
                    box_width,
                    box_width,
                    fill=color,
                    fill_opacity=opacity,
                    stroke=border,
                    stroke_width=1
                ))

            # Step right
            current_x += (box_width + gap)

    def mark_events(self, events, type_filter="D", color="red", shape="circle", size=3):
        """
        Draws symbols on the branches at the exact event times (Linear Layout).
        """
        name_to_node = {n.name: n for n in self.t.traverse()}

        for ev in events:
            if ev.get('type') != type_filter: continue

            node_name = str(ev['node'])
            node = name_to_node.get(node_name)
            if not node or node.is_root(): continue

            # 1. Get Coordinates
            # In Vertical drawer: coordinates = (x, y)
            x_child, y_child = node.coordinates
            x_parent, _ = node.up.coordinates  # Parent X is start of branch

            # The branch line sits at y_child height, running from x_parent to x_child

            # 2. Interpolate X based on Time
            dist_parent = node.up.dist_to_root
            dist_child = node.dist_to_root
            event_time = ev['time']

            if dist_child > dist_parent:
                fraction = (event_time - dist_parent) / (dist_child - dist_parent)
                fraction = max(0.0, min(1.0, fraction))

                final_x = x_parent + fraction * (x_child - x_parent)
            else:
                final_x = x_child

            # 3. Draw
            # Y is constant (y_child) for horizontal branches
            if shape == "circle":
                self.d.append(draw.Circle(final_x, y_child, size, fill=color))
            elif shape == "x":
                self.d.append(draw.Line(final_x - size, y_child - size, final_x + size, y_child + size, stroke=color,
                                        stroke_width=1))
                self.d.append(draw.Line(final_x + size, y_child - size, final_x - size, y_child + size, stroke=color,
                                        stroke_width=1))

    def _draw_internal_final(self, n, color, hide_line=False):
        x, y = n.coordinates

        # 1. Vertical Line (The "Split" bar)
        c1, c2 = n.get_children()  # Assuming bifurcating
        min_y = min([c.y_coord for c in n.get_children()])
        max_y = max([c.y_coord for c in n.get_children()])

        self.d.append(draw.Line(x, min_y, x, max_y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

        # 2. Node Circle
        self.d.append(draw.Circle(x, y, self.style.node_size, fill=color))

        # 3. Horizontal Line to Parent
        if not n.is_root() and not hide_line:
            p_x, p_y = n.up.coordinates
            self.d.append(draw.Line(p_x, y, x, y, stroke=color, stroke_width=self.style.branch_size, fill='none'))

        # 4. OPTIONAL: Root Stem
        elif n.is_root():
            # Draw a small line to the left (e.g., 20px)
            self.d.append(draw.Line(x - 20, y, x, y, stroke=color, stroke_width=self.style.branch_size, fill='none'))