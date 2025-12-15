import ete3
import drawsvg as draw
import math
import random
import pandas as pd
import numpy as np
import newick
import re
import copy
import os



def radial_converter(degree, radius, rotation = 0):    
    rotation -= 90
    x = math.sin(math.radians(degree) + math.radians(rotation)) * radius 
    y = math.cos(math.radians(degree) + math.radians(rotation)) * radius  
    return x, y

def radial_deconverter(x, y):     
    degree = math.degrees(math.atan(x/y))
    radius = math.sqrt(x**2 + y**2)     
    return degree, radius

def arc_converter(degree):
    x = 180 - degree     
    return x



def ale_parser(rec_file):

    with open(rec_file) as f:

        lines = f.readlines()
        stree = lines[2].strip()
        ll = lines[6].strip().split()[-1]
        dp,tp,lp = lines[8].strip().split("\t")[1:]
        n_reconciled_trees = int(lines[9].strip().split()[0])
        reconciled_trees = lines[11:n_reconciled_trees + 11]
        de,te,le,se = lines[11 + n_reconciled_trees + 1].split("\t")[1:]
        table = lines[11 + n_reconciled_trees + 3:]
        
    return stree, ll, (dp,tp,lp), reconciled_trees, table



class TreeDrawer():
    
    def __init__(self, tree, params):

        self.t      = tree
        self.params = params
        
        # If the total_length_of_tree parameter is == 0, use the age of the tree
        if self.params["total_length_of_tree"] == 0:
            self.total_length_of_tree = self.t.get_distance(self.t.get_leaves()[0])
        else:
            self.total_length_of_tree = self.params["total_length_of_tree"]            
            
        self.add_features_to_tree()        
        height = self.params["height"]
        width = self.params["width"]
        
        self.d = draw.Drawing(height, width, origin='center', displayInline=True,)    
        self.d.append(draw.Rectangle(-width,-height,height*2,width*2, fill="white"))
     
    def add_features_to_tree(self):
        
        radius = self.params["radius"]
        degrees = self.params["degrees"]
        
        leaves = self.t.get_leaves()
        n_leaves = len(leaves)
        adjust = (len(self.t) / 2) - 0.5
        self.arc_leaf = degrees / (n_leaves)       
        
        # First iteration. Leaves, coordinates
        
        for index, l in enumerate(self.t):                          
            branch_length = l.dist * radius / self.total_length_of_tree              
            l.add_feature("branch_length", branch_length)                        
            l.add_feature("coordinates",    (self.arc_leaf * index, radius,))             
            l.add_feature("eb_coordinates", (self.arc_leaf * index, radius - branch_length))
                        
        # Second iteration. Full tree, coordinates
        
        for n in self.t.traverse("postorder"):             
            if n.is_leaf():
                n.add_feature("age", 0)
            else:
                c1, c2 = n.get_children()
                n.add_feature("age", c1.age + c1.dist)
                
                d1, r1 = c1.coordinates
                d2, r2 = c2.coordinates
                de = (d1 + d2) / 2                
                branch_length = n.dist * radius / self.total_length_of_tree  
           
                n.add_feature("branch_length", branch_length)
                n.add_feature("coordinates", (de, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree)) 
                
    def draw(self, branch2color = None, ):   
        
        height = self.params["height"]
        width = self.params["width"]
        radius = self.params["radius"]
        degrees = self.params["degrees"]
        leaf_size = self.params["leaf_size"]
        leaf_color = self.params["leaf_color"]
        branch_size = self.params["branch_size"]
        branch_color = self.params["branch_color"]
        node_size = self.params["node_size"]
        rotation = self.params["rotation"]
        
        for n in self.t.traverse("postorder"): 
            
            if branch2color != None:
                branch_color = branch2color.get(n, self.params["branch_color"])
                if branch_color == "None":
                    continue
           
            if n.is_leaf():
                
                de, re =  n.coordinates                
                de2, re2 = n.eb_coordinates                                
                x, y =   radial_converter(de, re, rotation )
                xe, ye = radial_converter(de2, re2 - (branch_size / 2), rotation )     
                
                self.d.append(draw.Circle(x,y,leaf_size, fill = leaf_color)) 
                self.d.append(draw.Line(xe, ye, x, y, stroke=branch_color, stroke_width=branch_size, fill='none'))
                                
            else:
                
                c1, c2 = n.get_children()        
                d1,r1 = c1.coordinates
                d2,r2 = c2.coordinates                
                de = (d1 + d2) / 2
                mid, mxd = min([d1, d2]), max([d1, d2])
                
                x, y =   radial_converter(de,  (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree, rotation)
                
                if n.is_root():
                    print((self.total_length_of_tree - n.age) * radius / self.total_length_of_tree)
                    self.d.append(draw.ArcLine(0,0, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree, mid + rotation - 180, mxd + rotation - 180 , stroke=branch_color, stroke_width=branch_size, fill="None"))
                    # The node
                    self.d.append(draw.Circle(x,y,node_size, fill = branch_color)) 
                
                else:                   
                    
                    xe, ye = radial_converter(de,  (self.total_length_of_tree - (n.up).age) * radius / self.total_length_of_tree  - branch_size / 2, rotation)            
                    
                    # The horizontal line        
                    self.d.append(draw.ArcLine(0,0, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree, mid + rotation - 180, mxd + rotation - 180, stroke=branch_color, stroke_width=branch_size, fill="None"))        
                    
                    # The node
                    self.d.append(draw.Circle(x,y,node_size, fill = branch_color))      
                    
                    # The parent branch
                    self.d.append(draw.Line(xe, ye, x, y, stroke=branch_color, stroke_width=branch_size, fill='none'))
                        
            
    def add_ages(self, ages, stroke_width=1, color="grey", show_text =False, text_size = 9, degree = 0, x_adjust = 0, stroke_opacity=0.4): 
        
        radius = self.params["radius"]
        rotation = self.params["rotation"]
        
        for age in ages:
            adj_age = (radius / self.total_length_of_tree) * (self.total_length_of_tree - age)            
            self.d.append(draw.Circle(0, 0, adj_age, fill="None", stroke_width=stroke_width, stroke=color, stroke_opacity = stroke_opacity,))    

            if show_text:
                x, y = radial_converter(degree, adj_age , rotation = 180 + rotation)    
                self.d.append(draw.Text(str(age) + " mya", text_size, x + x_adjust, y,  fill='black'))  
    
    def add_shape(self, clade2shape, opacity = 1, stroke = "black", shape_size = 5):
        
        radius = self.params["radius"] 
        rotation = self.params["rotation"]
        
        for n, color in clade2shape.items():  
            
            de,r = n.coordinates            
            
            branch_length = n.dist * radius / self.total_length_of_tree             
            
            x, y = radial_converter  (de, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree, rotation)
            
            if n != self.t:
                xe, ye = radial_converter(de, (self.total_length_of_tree - n.up.age) * radius / self.total_length_of_tree , rotation)                                   
                self.d.append(draw.Circle((x + xe)/2,(y + ye)/2,shape_size, fill = color, stroke=stroke, opacity = opacity))
            else:
                self.d.append(draw.Circle(x,y,shape_size, fill = color, stroke=stroke, opacity = opacity))
                        
            
    def add_leaf_shape(self, clade2color, opacity = 1, stroke = "black", shape_size = 5, offset=0):
        
        radius = self.params["radius"] 
        rotation = self.params["rotation"]        
        for n, color in clade2color.items():              
            de,_ = n.coordinates                        
            x, y = radial_converter(de,  radius + offset, rotation )            
            self.d.append(draw.Circle(x,y,shape_size, fill = color, stroke=stroke))            

    def add_transfers(self, transfers, colors=("red", "red"), radius_thickness=2):
        
        radius = self.params["radius"] 
        rotation = self.params["rotation"]

        for donor, recipient, weight in transfers:  
            
            dn = self.t&donor
            rc = self.t&recipient
            
            dn_de, dn_r = dn.coordinates
            rc_de, rc_r = rc.coordinates           
                         
            mid, mxd = min([dn_de, rc_de]), max([dn_de, rc_de]) 
            
            # I should write this
            # If the branches overlap, make it arrive in the center of the overlapping
            # If the branches don't overlap, make it arrive at the center of the receptor branch
            
            midpoint = (rc.age + rc.up.age) / 2            
            position = (self.total_length_of_tree - midpoint) * radius / self.total_length_of_tree
                                
            dist = min(mxd-mid, mid+360-mxd)
            
            if mxd > mid:
                if mxd - mid > mid + 360 - mxd:
                    signeddist = mid + 360 - mxd 
                else:
                    signeddist = mid - mxd  
            else:
                if mid - mxd > mxd + 360 - mid:
                    signeddist = mxd + 360 - mid  
                else:
                    signeddist = mxd - mid             
            
            if signeddist <= 0:
                self.d.append(draw.ArcLine(0,0, position,  mxd + rotation - 180 , mid + rotation - 180 , stroke=colors[0], stroke_width=radius_thickness, fill="None", opacity=weight))        
            else:
                 self.d.append(draw.ArcLine(0,0, position, mid + rotation - 180 , mxd + rotation - 180, stroke=colors[1], stroke_width=radius_thickness, fill="None", opacity=weight))        


    def highlight_branch(self, n, opacity = 1, branch_color = "black", branch_size = 5):
        radius = self.params["radius"] 
        rotation = self.params["rotation"]
        
        if n.is_leaf():
            
            self.d.append(draw.Line(xe, ye, x, y, stroke=branch_color, stroke_width=branch_size, fill='none', opacity = opacity))
            
        else:
            c1, c2 = n.get_children()        
            d1,r1 = c1.coordinates
            d2,r2 = c2.coordinates                
            de = (d1 + d2) / 2
            x, y =   radial_converter(de, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree, rotation )
            xe, ye = radial_converter(de, (self.total_length_of_tree - n.up.age) * radius / self.total_length_of_tree, rotation )          

            self.d.append(draw.Line(xe, ye, x, y, stroke=branch_color, stroke_width=branch_size, fill='none', opacity = opacity))

    def gradient_branch(self, n, opacity = 1, branch_color = ("red","blue"), branch_size = 1):
        
        background_branch_size = self.params["branch_size"]
        radius = self.params["radius"]  
        rotation = self.params["rotation"]
                
        d_n,r = n.coordinates 
        
        x, y =   radial_converter(d_n, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree, rotation )
        xe, ye = radial_converter(d_n, (self.total_length_of_tree - n.up.age) * radius / self.total_length_of_tree - (background_branch_size / 2), rotation )
        
        mgradient = draw.LinearGradient(xe,ye,x,y)               
        mgradient.add_stop(0, branch_color[0], 1)
        mgradient.add_stop(1, branch_color[1], 1)                        

        self.d.append(draw.Line(xe, ye, x, y, stroke=mgradient, stroke_width=branch_size, fill='none', opacity = opacity))        
        
        
    def color_background(self, clade2bg, opacity = 0.5, gradient=False, gradient_stop=0.3, color_stem=False):
        
        radius = self.params["radius"]
        branch_color = self.params["branch_color"]
        rotation = self.params["rotation"]
    
        for n, color in clade2bg.items():
            
            if n.is_leaf():
                continue                               
            
            d_n,r = n.coordinates                    
            cs = [l.coordinates[0] for l in n.get_leaves()]   
                
            if color_stem == True:
                size = (self.total_length_of_tree - n.up.age) *  radius / self.total_length_of_tree  
            else:
                size = (self.total_length_of_tree - n.age)    *  radius / self.total_length_of_tree  
            
            
            r2 = 180 - min(cs) + (self.arc_leaf/2)  - rotation 
            r1 = 180 - max(cs) - (self.arc_leaf/2)  - rotation             
            
            if gradient == True:                
                mgradient = draw.RadialGradient(0,0,radius)
                mgradient.add_stop(0, color, 0)
                mgradient.add_stop(size * gradient_stop, color, opacity)                
                p = draw.Path(fill=mgradient, stroke=branch_color, stroke_width=0,)                   
                
            else:
                p = draw.Path(fill=color, stroke=branch_color, stroke_width=0, fill_opacity=opacity)                   
                    
            p.arc(0,0,  radius,  r2,  r1, cw=False )
            p.arc(0,0,  size,    r1,  r2, cw=True, include_l=True)         
            
            self.d.append(p)
            
              
    def add_names(self, clade2name, text_size=12, x_adjust=0, radius_adjust = 0):
        
        radius = self.params["radius"]
        rotation = self.params["rotation"]
        
        for clade, name in clade2name.items():
            
            coordinates = list()
            
            for des in clade:
                de,di = des.coordinates
                coordinates.append(de)        

            x, y = radial_converter((max(coordinates) + min(coordinates)) / 2, radius + radius_adjust , rotation)    
            self.d.append(draw.Text(name, text_size, x + x_adjust, y,  fill='black'))          
            
            
    def add_uncertainty(self, n, ci, color = "grey", uwidth = 0, opacity = 0.5):
        
        # This uses arcs and not many lines
        
        height = self.params["height"]
        width = self.params["width"]
        radius = self.params["radius"]
        degrees = self.params["degrees"]
        rotation = self.params["rotation"]
        
        c1, c2 = n.get_children()                         
        d1, r1 = c1.coordinates # Degrees, radius
        d2, r2 = c2.coordinates # Degrees, radius        
        mid, mxd = min([d1, d2]), max([d1, d2]) 
        minv, maxv = ci
                
        lower_bound = (self.total_length_of_tree - float(minv)) * radius / self.total_length_of_tree     
        upper_bound = (self.total_length_of_tree - float(maxv)) * radius / self.total_length_of_tree         
        
        r2 = 180 - mid + uwidth - rotation 
        r1 = 180 - mxd - uwidth - rotation          
                    
        p = draw.Path(fill=color, stroke=color, stroke_width=0, fill_opacity=opacity)                 
        
        p.arc(0,0, upper_bound , r2, r1, cw = False)
        p.arc(0,0, lower_bound , r1, r2, cw=True, include_l=True)         

        self.d.append(p)
        
    def add_maxLL_age(self, n, age, color = "red", uwidth = 0, opacity = 0.7, thickness = 10):
        
        # This uses arcs and not many lines
        
        height = self.params["height"]
        width = self.params["width"]
        radius = self.params["radius"]
        degrees = self.params["degrees"]
        rotation = self.params["rotation"]
        
        c1, c2 = n.get_children()                         
        d1, r1 = c1.coordinates # Degrees, radius
        d2, r2 = c2.coordinates # Degrees, radius        
        mid, mxd = min([d1, d2]), max([d1, d2]) 
        
        minv, maxv = age - thickness, age + thickness
                
        lower_bound = (self.total_length_of_tree - float(minv)) * radius / self.total_length_of_tree     
        upper_bound = (self.total_length_of_tree - float(maxv)) * radius / self.total_length_of_tree         
        
        r2 = 180 - mid + uwidth - rotation 
        r1 = 180 - mxd - uwidth - rotation          
                    
        p = draw.Path(fill=color, stroke=color, stroke_width=0, fill_opacity=opacity)                 
        
        p.arc(0,0, upper_bound , r1, r2 )
        p.arc(0,0, lower_bound , r2, r1, cw=True, include_l=True)         

        self.d.append(p)       
        
    
    def add_external_arcs(self, clade2color, adj_position = 0, radius_thickness = 1, adj_padding = 0): 

        radius = self.params["radius"]
        rotation = self.params["rotation"]
 
        for n, color in clade2color.items():   
            
            cs = [l.coordinates[0] for l in n.get_leaves()]    
            mid, mxd = min(cs), max(cs) 
            position = (radius / self.total_length_of_tree) * (self.total_length_of_tree + adj_position)   
            self.d.append(draw.ArcLine(0,0, position, mid + rotation - 180 - adj_padding , mxd + rotation - 180 + adj_padding , stroke=color, stroke_width=radius_thickness, fill="None", opacity=1))
            
            
            
    
    def add_external_info(self, clade2color, offset = 10, radius_thickness = 1):
        
        radius = self.params["radius"] 
        rotation = self.params["rotation"]
        
        for n, color in clade2color.items():  
            
            de,_ = n.coordinates                        
            
            p = draw.Path(fill=color, stroke=color, stroke_width=0)                   
            
            r2 = 180 - de + (self.arc_leaf/2) - rotation 
            r1 = 180 - de - (self.arc_leaf/2) - rotation
            
            p.arc(0,0, radius + offset - (radius_thickness / 2), r2, r1, cw=False )
            p.arc(0,0, radius + offset + (radius_thickness / 2), r1, r2, cw=True, include_l=True)         
            
            self.d.append(p)
    
    def add_text(self, text, x =0, y=0, text_size = 12, color="black"):        
        self.d.append(draw.Text(text, text_size, x, y,  fill=color))
        
    def add_leaf_names(self, mapping = None, text_size = 12, padding = 0, ignore = 0):
        i = 0
        rotation = self.params["rotation"]
        if mapping is None:            
            for l in self.t:            
                de, re = l.coordinates
                
                # 1. Calculate the final visual angle in degrees (0-360 range)
                # We assume 'de' is in degrees. If 'de' is radians, convert it first.
                visual_angle = (de + rotation) % 360
                
                # 2. Define start (node) and end (outer) coordinates
                # Using the longer length (300) we fixed in the previous step
                x_node, y_node = radial_converter(de, re + padding, rotation)
                x_outer, y_outer = radial_converter(de, re + padding + 300, rotation)                
                
                p = draw.Path(stroke_width=0, fill='black', fill_opacity=0.2)
                
                # 3. Check if we are on the "left" side (90 to 270 degrees)
                if 90 < visual_angle < 270:
                    # LEFT SIDE: Flip!
                    # Draw path from Outer -> Node (inwards)
                    p.M(x_outer, y_outer).L(x_node, y_node)
                    anchor = 'end'  # Anchor text at the end of the path (at the node)
                    
                    # Optional: tweak alignment slightly so it doesn't touch the node
                    # You might need a small offset here if it touches the tip too closely
                else:
                    # RIGHT SIDE: Standard
                    # Draw path from Node -> Outer (outwards)
                    p.M(x_node, y_node).L(x_outer, y_outer)
                    anchor = 'start' # Anchor text at the start of the path (at the node)
    
                i += 1
                
                if ignore != 0:
                    if i % ignore == 0: # I also fixed the modulo operator for you here
                         self.d.append(draw.Text(l.name, text_size, path=p, text_anchor=anchor, line_height=1, center=True))
                else:
                    # Use the dynamic 'anchor' variable we set above
                    self.d.append(draw.Text(l.name, text_size, path=p, text_anchor=anchor, line_height=1, center=True))
                
    def add_inner_names(self, mapping = None,  text_size = 12, radius_size = 10, circle_color ="black", text_color="black"):
        
        rotation = self.params["rotation"]
        
        if mapping == None:            
            for n in self.t.traverse():
                if n.is_leaf():        
                    continue
                de, re =  n.coordinates 
                x, y =  radial_converter(de, re, rotation)                
                
                self.d.append(draw.Circle(x, y, r=radius_size, fill='black'))
                self.d.append(draw.Text(str(n.name), text_size, x - (text_size/3), y - (text_size/3),  fill='white',  ))
                
        else:
            for n, name in mapping.items():
                
                de, re =  n.coordinates 
                x, y =  radial_converter(de, re, rotation)                
                
                self.d.append(draw.Circle(x, y, r=radius_size, fill=circle_color))
                self.d.append(draw.Text(name, text_size, x - (text_size/3), y - (text_size/3),  fill=text_color,  ))

    def add_heatmap_ring(self, mapping, padding=50, width=20, stroke_color="none"):
        
        radius = self.params["radius"]
        rotation = self.params["rotation"]
        
        # 1. Calculate Min and Max for Normalization
        # Filter mapping to only include leaves actually in the tree
        valid_values = [v for k, v in mapping.items() if k in [l.name for l in self.t]]
        
        if not valid_values:
            print("Warning: No matching leaves found in mapping.")
            return

        min_val = min(valid_values)
        max_val = max(valid_values)
        
        # Avoid division by zero if all values are identical
        if max_val == min_val:
            denom = 1
        else:
            denom = max_val - min_val

        # 2. Iterate over leaves and draw arcs
        for l in self.t:
            if l.name not in mapping:
                continue # Or you could draw a default color here
            
            val = mapping[l.name]
            
            # Normalize value between 0 and 1
            norm = (val - min_val) / denom
            
            # Calculate Grayscale Color (White to Black)
            # 0 -> White (255), 1 -> Black (0)
            gray_int = int(255 * (1 - norm))
            hex_color = '#%02x%02x%02x' % (gray_int, gray_int, gray_int)
            
            # Get Leaf Coordinates
            de, re = l.coordinates
            
            # Calculate Arc Angles
            # We subtract/add half the arc width to cover the full space of the leaf
            start_angle = de - (self.arc_leaf / 2) + rotation - 180
            end_angle   = de + (self.arc_leaf / 2) + rotation - 180
            
            # Calculate Radial Position
            # We add padding + half the width because ArcLine draws the stroke centered on the radius
            arc_radius = radius + padding + (width / 2)
            
            # Draw the Arc segment
            self.d.append(draw.ArcLine(
                0, 0, 
                arc_radius, 
                start_angle, 
                end_angle, 
                stroke=hex_color, 
                stroke_width=width, 
                fill="none"
            ))
            
            # Optional: Add a border around the ring segments
            if stroke_color != "none":
                 self.d.append(draw.ArcLine(
                0, 0, 
                arc_radius, 
                start_angle, 
                end_angle, 
                stroke=stroke_color, 
                stroke_width=1, 
                fill="none"
            ))
           
        
        
class RealTreeDrawer(): # This is to plot real branch length
    
    def __init__(self, tree, params):

        self.t      = tree
        self.params = params
            
        self.add_features_to_tree()        
        
        height = self.params["height"]
        width = self.params["width"]
        
        self.d = draw.Drawing(height, width, origin='center', displayInline=True,)    
        self.d.append(draw.Rectangle(-width,-height,height*2,width*2, fill="white"))
     
    def add_features_to_tree(self):
        
        radius = self.params["radius"]
        degrees = self.params["degrees"]
        
        leaves = self.t.get_leaves()
        n_leaves = len(leaves)
        adjust = (len(self.t) / 2) - 0.5
        self.arc_leaf = degrees / (n_leaves)   
        
        # zero iteration. We get what is the most distant leaves
        
        self.t.add_feature("dist_to_root", 0)
        
        dists = list()        
        for n in self.t.traverse("preorder"):                        
            if n.is_root():
                continue            
            
            n.add_feature("dist_to_root", (n.up).dist_to_root + n.dist )
            
            if n.is_leaf():
                dists.append((n, n.dist_to_root))
                
                
        self.total_length_of_tree = max(dists, key=lambda x:x[1])[1]
        self.bf = radius / self.total_length_of_tree
        
        # First iteration. Leaves, coordinates
        
        for index, l in enumerate(self.t):
            
            branch_length = l.dist * self.bf
            
            l.add_feature("branch_length",  branch_length)                        
            l.add_feature("coordinates",    (self.arc_leaf * index, l.dist_to_root * self.bf,))             
            l.add_feature("eb_coordinates", (self.arc_leaf * index, (l.up).dist_to_root * self.bf))
                        
        # Second iteration. Full tree, coordinates
        
        for n in self.t.traverse("postorder"):             
            if n.is_leaf():
                n.add_feature("age", 0)
            else:
                c1, c2 = n.get_children()
                n.add_feature("age", c1.age + c1.dist)
                
                d1, r1 = c1.coordinates
                d2, r2 = c2.coordinates
                de = (d1 + d2) / 2                
                branch_length = n.dist * radius / self.total_length_of_tree  
           
                n.add_feature("branch_length", branch_length)
                n.add_feature("coordinates", (de, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree)) 
                
                
                
    def draw(self, branch2color = None, ):   
        
        height = self.params["height"]
        width = self.params["width"]
        radius = self.params["radius"]
        degrees = self.params["degrees"]
        leaf_size = self.params["leaf_size"]
        leaf_color = self.params["leaf_color"]
        branch_size = self.params["branch_size"]
        branch_color = self.params["branch_color"]
        node_size = self.params["node_size"]
        rotation = self.params["rotation"]
        
        for n in self.t.traverse("postorder"): 
            
            if branch2color != None:
                branch_color = branch2color.get(n, self.params["branch_color"])
                if branch_color == "None":
                    continue
           
            if n.is_leaf():
                
                de, re =  n.coordinates                
                de2, re2 = n.eb_coordinates                                
                x, y =   radial_converter(de, re, rotation )
                xe, ye = radial_converter(de2, re2 - (branch_size / 2), rotation )     
                
                self.d.append(draw.Circle(x,y,leaf_size, fill = leaf_color)) 
                self.d.append(draw.Line(xe, ye, x, y, stroke=branch_color, stroke_width=branch_size, fill='none'))
                                
            else:
                                
                c1, c2 = n.get_children()        
                d1,r1 = c1.coordinates
                d2,r2 = c2.coordinates                
                de = (d1 + d2) / 2
                mid, mxd = min([d1, d2]), max([d1, d2])
                
                x, y =   radial_converter(de,  n.dist_to_root * self.bf, rotation)
                
                
                if n.is_root():                    
                    continue
                    #self.d.append(draw.ArcLine(0,0, (self.total_length_of_tree - n.age) * radius / self.total_length_of_tree, mid + rotation - 180, mxd + rotation - 180 , stroke=branch_color, stroke_width=branch_size, fill="None"))
                    # The node
                    #self.d.append(draw.Circle(x,y,node_size, fill = branch_color)) 
                
                else:                  
                    
                    xe, ye =   radial_converter(de,  ((n.up).dist_to_root * self.bf) - (branch_size / 2), rotation)                                        
                    # The horizontal line        
                    self.d.append(draw.ArcLine(0,0, n.dist_to_root * self.bf, mid + rotation - 180, mxd + rotation - 180, stroke=branch_color, stroke_width=branch_size, fill="None"))                            
                    # The node
                    self.d.append(draw.Circle(x,y,node_size, fill = branch_color))      
                    
                    # The parent branch
                    self.d.append(draw.Line(xe, ye, x, y, stroke=branch_color, stroke_width=branch_size, fill='none'))
    
    def add_support(self, support_threshold, fill, size=2, stroke_width=0, stroke="black"):
        rotation = self.params["rotation"]
        for n in self.t.traverse():
            if n.is_leaf():
                continue
            else:
                try:
                    node_support = float(n.name)
                    if float(n.name) >= support_threshold:
                        de, re =  n.coordinates                                    
                        x, y =   radial_converter(de,  n.dist_to_root * self.bf, rotation)
                        self.d.append(draw.Circle(x,y,size, fill =fill, stroke_width=stroke_width, stroke=stroke)) 
                except:
                    pass
                            
                 
            
    def color_background(self, clade2bg, offset=0, opacity = 0.5, gradient=False, gradient_stop=0.3, color_stem=False):
        
        radius = self.params["radius"]
        branch_color = self.params["branch_color"]
        rotation = self.params["rotation"]
    
        for n, color in clade2bg.items():
            
            if n.is_leaf():
                continue                               
            
            d_n,r = n.coordinates                    
            cs = [l.coordinates[0] for l in n.get_leaves()]   
                
            if color_stem == True:
                size = (self.total_length_of_tree - n.up.age) *  self.bf
            else:
                size = (self.total_length_of_tree - n.age)    *  self.bf
            
            
            r2 = 180 - min(cs) + (self.arc_leaf/2)  - rotation 
            r1 = 180 - max(cs) - (self.arc_leaf/2)  - rotation             
            
            if gradient == True:                
                mgradient = draw.RadialGradient(0,0,radius)
                mgradient.add_stop(0, color, 0)
                mgradient.add_stop(size * gradient_stop, color, opacity)                
                p = draw.Path(fill=mgradient, stroke=branch_color, stroke_width=0,)                   
                
            else:
                p = draw.Path(fill=color, stroke=branch_color, stroke_width=0, fill_opacity=opacity)                   
                    
            p.arc(0,0,  radius,  r2,  r1, cw=False )
            p.arc(0,0,  size,    r1,  r2, cw=True, include_l=True)         
            
            self.d.append(p)
            
    def color_background(self, clade2bg, offset=0, opacity = 0.5, beginning = 0, gradient=False, gradient_stop=0.3, color_stem=False):
        
        radius = self.params["radius"]
        branch_color = self.params["branch_color"]
        rotation = self.params["rotation"]
    
        for n, color in clade2bg.items():
            
            if n.is_leaf():
                continue                               
            
            d_n,r = n.coordinates                    
            cs = [l.coordinates[0] for l in n.get_leaves()]   
                
            if color_stem == True:
                size = (self.total_length_of_tree - n.up.age) *  self.bf
            else:
                size = (self.total_length_of_tree - n.age)    *  self.bf
            
            
            r2 = 180 - min(cs) + (self.arc_leaf/2)  - rotation 
            r1 = 180 - max(cs) - (self.arc_leaf/2)  - rotation             
            
            if gradient == True:                
                mgradient = draw.RadialGradient(0,0,radius)
                mgradient.add_stop(0, color, 0)
                mgradient.add_stop(size * gradient_stop, color, opacity)                
                p = draw.Path(fill=mgradient, stroke=branch_color, stroke_width=0,)                   
                
            else:
                p = draw.Path(fill=color, stroke=branch_color, stroke_width=0, fill_opacity=opacity)                   
                    
            p.arc(0,0,  radius - offset,  r2,  r1, cw=False )
            p.arc(0,0,  beginning,    r1,  r2, cw=True, include_l=True)         
            
            self.d.append(p)        
    
    def add_names(self, clade2name, text_size=12, x_adjust=0, radius_adjust = 0):
        
        radius = self.params["radius"]
        rotation = self.params["rotation"]
        
        for clade, name in clade2name.items():
            
            coordinates = list()
            
            for des in clade:
                de,di = des.coordinates
                coordinates.append(de)        

            x, y = radial_converter((max(coordinates) + min(coordinates)) / 2, radius + radius_adjust , rotation)    
            self.d.append(draw.Text(name, text_size, x + x_adjust, y,  fill='black'))          
            
    
    def add_external_arcs(self, clade2color, adj_position = 0, radius_thickness = 1, adj_padding = 0): 

        radius = self.params["radius"]
        rotation = self.params["rotation"]
 
        for n, color in clade2color.items():   
                    
            color = "black"            
            cs = [l.coordinates[0] for l in n.get_leaves()]    
            mid, mxd = min(cs), max(cs) 
            position = self.bf * (radius + adj_position)   
            self.d.append(draw.ArcLine(0,0, position, mid + rotation - 180 - adj_padding , mxd + rotation - 180 + adj_padding , stroke=color, stroke_width=radius_thickness, fill="None", opacity=1))
            
            
    def add_external_info(self, clade2color, offset = 10, radius_thickness = 1):
        
        radius = self.params["radius"] 
        rotation = self.params["rotation"]
        
        for n, color in clade2color.items():  
            
            de,_ = n.coordinates                        
            
            p = draw.Path(fill=color, stroke=color, stroke_width=0)                   
            
            r2 = 180 - de + (self.arc_leaf/2) - rotation 
            r1 = 180 - de - (self.arc_leaf/2) - rotation
            
            p.arc(0,0, radius + offset - (radius_thickness / 2), r2, r1, cw=False )
            p.arc(0,0, radius + offset + (radius_thickness / 2), r1, r2, cw=True, include_l=True)         
            
            self.d.append(p)
    
    def add_text(self, text, x =0, y=0, text_size = 12, color="black"):        
        self.d.append(draw.Text(text, text_size, x, y,  fill=color))
        
    def add_leaf_names(self, mapping = None,  text_size = 12, padding = 0, ignore = 0):
        i = 0
        rotation = self.params["rotation"]
        if mapping == None:            
            for l in self.t:           
                de, re =  l.coordinates                 
                x, y =  radial_converter(de, re + padding, rotation)
                x2, y2 =  radial_converter(de, re + padding + 350, rotation)                
                p = draw.Path(stroke_width=0, fill='black', fill_opacity=0.2)
                p.M(x, y).L(x2, y2)                                
                i+=1
                
                if ignore != 0:
                    if ignore & i == 0:
                        self.d.append(draw.Text(l.name, text_size, path=p, text_anchor='start', line_height=1))
                    else:
                        continue
                else:
                    self.d.append(draw.Text(l.name, text_size, path=p, text_anchor='start', line_height=1))
                #self.d.append(draw.Text(l.name,  text_size, 0, 0,  fill='black',  transform=f"translate({x},{y}) rotate(0)"))
                #self.d.append(draw.Text(l.name, text_size, x, y,  fill='black',))
                
    def add_inner_names(self, mapping = None,  text_size = 12, radius_size = 10, circle_color ="black", text_color="black"):
        
        rotation = self.params["rotation"]
        
        if mapping == None:            
            for n in self.t.traverse():
                if n.is_leaf():        
                    continue
                de, re =  n.coordinates 
                x, y =  radial_converter(de, re, rotation)                
                
                self.d.append(draw.Circle(x, y, r=radius_size, fill='black'))
                self.d.append(draw.Text(str(n.name), text_size, x - (text_size/3), y - (text_size/3),  fill='white',  ))
                
        else:
            for n, name in mapping.items():
                
                de, re =  n.coordinates 
                x, y =  radial_converter(de, re, rotation)                
                
                self.d.append(draw.Circle(x, y, r=radius_size, fill=circle_color))
                self.d.append(draw.Text(name, text_size, x - (text_size/3), y - (text_size/3),  fill=text_color,  ))
    
    def gradient_branch(self, n, opacity = 1, branch_color = ("red","blue"), branch_size = 1):
        
        background_branch_size = self.params["branch_size"]
        radius = self.params["radius"]  
        rotation = self.params["rotation"]
                
        de,r = n.coordinates 
        
        x, y =     radial_converter(de,  n.dist_to_root * self.bf, rotation)
        xe, ye =   radial_converter(de,  ((n.up).dist_to_root * self.bf) - (branch_size / 2), rotation)
        
        mgradient = draw.LinearGradient(xe,ye,x,y)               
        mgradient.add_stop(0, branch_color[0], 1)
        mgradient.add_stop(1, branch_color[1], 1)  
        
        self.d.append(draw.Line(xe, ye, x, y, stroke=mgradient, stroke_width=branch_size, fill='none', opacity = opacity))   
        
    def add_nucleotide_scale(self, x, y, length, text_size = 12, x_adjust = 10):
        
        
        self.d.append(draw.Line(x, y, x+(self.bf*length), y, stroke="black", stroke_width=2, fill='none'))   
        self.d.append(draw.Text(str(length), text_size, x + x_adjust, y + 12,  fill='black'))          
        
        
        
         
    
    
    
class TreeMovie():
    def __init__(self, trees, params, frames):
            
        # It receives a list of trees and it gets the movie interpolating them        
        # First we get the first tree
         
        all_frames = list()
        self.all_images = list()
        
        for tree1, tree2 in zip(trees, trees[1:]):                
            all_frames += self.interpolation(tree1, tree2, frames)
            
        for frame in all_frames:
            td = TreeDrawer(frame, params)
            td.draw()
            self.all_images.append(td.d)
    
    
    def interpolation(self, tree1, tree2, frames):
        
        interpolated_trees = list()        
        for frame in range(frames):
            interpolated_tree = copy.deepcopy(tree1)
            for n1 in interpolated_tree.traverse():
                
                n2 = tree2&n1.name            
                tdiff = n2.dist - n1.dist            
                frame_diff = tdiff / frames
                n1.dist += (frame_diff * frame)
            interpolated_trees.append(interpolated_tree)           
        return interpolated_trees
        
    def export(self, folder):        
        for frame, image in enumerate(self.all_images):        
            image.setPixelScale(2)  # Set number of pixels per geometry unit
            image.savePng(os.path.join(folder, f'frame_{frame}_.png'))
            
            
    def add_node_names(self):
        
        
        pass
        

class VerticalPlotter():
    def __init__(self, tree, params):
        
        self.params  = params
        self.height = self.params["height"] 
        self.width  = self.params["width"]  
        self.d = draw.Drawing(self.params["width"], self.params["height"], origin='center', displayInline=True, fill="white")        
        self.t = tree                
        self.n_leaves = len(self.t)
        self.d.append(draw.Rectangle(-self.width/2,-self.height/2, self.width, self.height, fill="white")) # Background        
        
    def draw(self, branch2color = None):
        
        hpadding = self.params["hpadding"] 
        vpadding = self.params["vpadding"] 
        node_color  =  self.params["node_color"]
        branch_size =  self.params["branch_size"]
        branch_color = self.params["branch_color"]
        
        leaf_spacing  = (self.width - hpadding) / (len(self.t) + 1) 
        

        branch_factor = (self.height - vpadding) / self.t.get_distance(self.t.get_leaves()[0])
        self.bf = branch_factor

        # We place the leaves
        
        for i,l in enumerate(self.t):
            
            xcoor = (-self.width/2)  + hpadding/2 + (leaf_spacing * i)
            ycoor =  self.height / 2 - (vpadding/2)
            #self.d.append(draw.Circle(xcoor, ycoor, 1, fill=node_color)) ## TO DRAW THE CIRCLES AT THE LEAVES
            l.add_feature("xcoor", xcoor)
            l.add_feature("ycoor", ycoor)
                        
        # We place the inner nodes
        
        for n in self.t.traverse("postorder"):
            if n.is_leaf():
                continue
            else:
                c1, c2 =  n.get_children()
                xcoor =  (c1.xcoor + c2.xcoor) / 2
                ycoor = -(n.get_distance(n.get_leaves()[0]) * branch_factor) + self.height/2 - (vpadding/2)       
                n.add_feature("xcoor", xcoor)
                n.add_feature("ycoor", ycoor)
                #self.d.append(draw.Circle(xcoor, ycoor, 3, fill="red")) # TO DRAW THE INNER NODES

        # The branches
        
        for n in self.t.traverse():
            
            if branch2color != None:
                branch_color = branch2color.get(n, self.params["branch_color"])
            
            if n.is_root():
                c1,c2 = n.get_children()
                self.d.append(draw.Line(c1.xcoor - branch_size/2, n.ycoor, c2.xcoor + branch_size/2, n.ycoor,stroke_width=branch_size,     stroke=branch_color))
            else:
                
                # Vertical lines  
                self.d.append(draw.Line(n.xcoor, n.ycoor, n.xcoor, n.up.ycoor,stroke_width=branch_size, stroke=branch_color))
                if n.is_leaf():
                    continue
                else:
                    # Horizontal lines
                    c1,c2 = n.get_children()
                    self.d.append(draw.Line(c1.xcoor - branch_size/2, n.ycoor, c2.xcoor + branch_size/2, n.ycoor,stroke_width=branch_size, stroke=branch_color))
        

    def add_labels(self, inner = False, x_adjust=0, y_adjust=0, at_center=False, text_size=10):
        
        text_color = "black"        
        for n in self.t.traverse():
            if n.is_leaf():
                self.d.append(draw.Text(f"{n.name}", text_size, 0, 0, transform=f"translate({n.xcoor - text_size/3 },{n.ycoor + 5}),rotate(90)", fill=text_color))
            else:
                if inner:
                    # We get the mean xcoordinate of the leaves:
                    if at_center:
                        self.d.append(draw.Text(f"{n.name}", text_size, 0, 0, transform=f"translate({n.xcoor - text_size/3 + x_adjust},{n.ycoor + y_adjust}),rotate(90)", fill=text_color))
                    else:
                        mean_x = np.mean([l.xcoor for l in n.get_leaves()])
                        self.d.append(draw.Text(f"{n.name}", text_size, 0, 0, transform=f"translate({mean_x - text_size/3 + x_adjust},{n.ycoor + y_adjust}),rotate(90)", fill=text_color))
    

    def add_labels_only_inner(self,  x_adjust=0, y_adjust=0, at_center=False):
        text_size = 10
        text_color = "black"        
        for n in self.t.traverse():
            if n.is_leaf():
                continue
            if at_center:
                self.d.append(draw.Text(f"{n.name}", text_size, 0, 0, transform=f"translate({n.xcoor - text_size/3 + x_adjust},{n.ycoor + y_adjust}),rotate(90)", fill=text_color))
            else:
                mean_x = np.mean([l.xcoor for l in n.get_leaves()])
                self.d.append(draw.Text(f"{n.name}", text_size, 0, 0, transform=f"translate({mean_x - text_size/3 + x_adjust},{n.ycoor + y_adjust}),rotate(90)", fill=text_color))
        
    
    def add_labels_at_tips(self, n2name, inner = False, x_adjust=0, y_adjust=0, offset_line = 0, text_size=10, add_border = False, stroke_width = 1):
        
        ycoor_oneleaf = (self.t.get_leaves()[0]).ycoor
        text_color = "black"        
        
        for n, name in n2name.items():
            
            xcoors = [l.xcoor for l in n.get_leaves()]
            mean_x = np.mean(xcoors)
            
            self.d.append(draw.Text(f"{name}", text_size, 0, 0, transform=f"translate({mean_x}, {ycoor_oneleaf + y_adjust}),rotate(90)", fill=text_color))
            
            if add_border == True:
                self.d.append(draw.Line(min(xcoors),ycoor_oneleaf + offset_line,max(xcoors),ycoor_oneleaf + offset_line, fill="None", stroke_width=stroke_width, stroke="black" ))    
     
    def add_text(self, text, x =0, y=0, text_size = 12):        
        self.d.append(draw.Text(text, text_size, x, y,  fill='black'))
        

    def add_shade(self,x,y,width,height, fill="black", opacity=1 ):
        self.d.append(draw.Rectangle(x,y,width,height, fill=fill, opacity=opacity))
    
    
    def add_shape_node(self, clade2color, opacity = 1, stroke = "black", shape_size = 5):                
        for n, color in clade2color.items():           
            x, y =   n.xcoor, n.ycoor
            self.d.append(draw.Circle(x,y,shape_size, fill = color, stroke=stroke, opacity = opacity))
            
    def add_shape_node_and_age(self, clade, age, color="black", opacity = 1, stroke = "black", shape_size = 5):                
       
        present = self.t.get_leaves()[0].ycoor
        start   = self.t.ycoor
        total_length_of_tree = self.t.get_distance(self.t.get_leaves()[0])
          
        hpadding = self.params["hpadding"] 
        vpadding = self.params["vpadding"] 
        x, y =   n.xcoor, n.ycoor
        adj_age = self.height/2 - vpadding/2 - (age * (present - start)) / total_length_of_tree
        self.d.append(draw.Circle(x,adj_age,shape_size, fill = color, stroke=stroke, opacity = opacity))
    
        
    def add_shape_halfbranch(self, clade2color, opacity = 1, stroke = "black", shape_size = 5):
                
        for n, color in clade2color.items():           
            x, y =   n.xcoor, n.ycoor
            ye = (n.up).ycoor
            self.d.append(draw.Circle(x,(y + ye)/2,shape_size, fill = color, stroke=stroke, opacity = opacity))

    def add_annotations_leaves(self, clade2color, length =10,  offset = 10, stroke_width = 1):
                
        for n, color in clade2color.items():    
            x, y =   n.xcoor, n.ycoor
            x = x - (stroke_width/2)                        
            self.d.append(draw.Line(x,y+offset,x,y+offset+length, fill="None", stroke_width=stroke_width, stroke=color, ))    
    
    
    def add_ages_small_text(self, ages, xcoor = 0, text_size = 9): 
        
        hpadding = self.params["hpadding"] 
        vpadding = self.params["vpadding"]         
        present = self.t.get_leaves()[0].ycoor
        start   = self.t.ycoor
        total_length_of_tree = self.t.get_distance(self.t.get_leaves()[0])

        for age in ages:
            adj_age = self.height/2 - vpadding/2 - (age * (present - start)) / total_length_of_tree            
            self.d.append(draw.Text(str(int(round(age/1000,1))), text_size, 0,0, transform=f"translate({xcoor},{adj_age}),rotate({90})",  fill='black'))  

    
    def add_ages(self, ages, stroke_width=1, color="grey", show_text =False, cut_limits = 10, xcoor = 0, text_size = 9, degree = 0, stroke_opacity=0.4): 
        
        hpadding = self.params["hpadding"] 
        vpadding = self.params["vpadding"] 
        
        present = self.t.get_leaves()[0].ycoor
        start   = self.t.ycoor
        total_length_of_tree = self.t.get_distance(self.t.get_leaves()[0])

        for age in ages:
            adj_age = self.height/2 - vpadding/2 - (age * (present - start)) / total_length_of_tree            
            self.d.append(draw.Line((-self.width/2) + cut_limits, adj_age, (self.width/2) - cut_limits, adj_age, fill="None", stroke_width=stroke_width, stroke=color, stroke_opacity = stroke_opacity,))    
            if show_text:            
                self.d.append(draw.Text(str(age) + " mya", text_size, xcoor, adj_age + text_size,  fill='black'))  
                
    
    def gradient_branch(self, n, opacity = 1, branch_color = ("red","blue"), branch_size = 1, dashed = False, pattern="5,5", uneven=False):
        
        background_branch_size = self.params["branch_size"]
                
        x, y =   n.xcoor, n.ycoor  
        xe, ye = n.xcoor, (n.up).ycoor
        
        mgradient = draw.LinearGradient(xe,ye,x,y) 
        
        if uneven == True:            
            mgradient.add_stop(0,   branch_color[0], 1)
            mgradient.add_stop(0.2, branch_color[0], 1)
            mgradient.add_stop(0.4, branch_color[1], 1)
            mgradient.add_stop(1,   branch_color[1], 1)            
            
        else:                                      
            mgradient.add_stop(0, branch_color[0], 1)
            mgradient.add_stop(1, branch_color[1], 1)                        
        
        line = draw.Line(xe, ye, x, y, stroke=mgradient, stroke_width=branch_size, fill='none', opacity=opacity)
    
        if dashed:            
            line.args['stroke-dasharray'] = pattern 
    
        self.d.append(line)
        
    
    def add_bw_scale(self, text_size = 20, x_adj = 0):
        
        one_leaf = self.t.get_leaves()[0]
        y =   one_leaf.ycoor - (self.bf * 4600)
        x = -(self.width)/2 + x_adj
        
        gd = [ (4600,4000, "Hadean",   "white"),
               (4000,2500, "Archean",  "black"),
               (2500,1600, "Paleoproterozoic",    "white"),
               (1600,1000, "Mesoprot.",     "black"),
               (1000,538.8, "Neoprot.",     "white"),
               (538.8,0, "Phanerozoic", "black"),
             ]
        
        for start, end, name, color in gd:
          
            width = 30
            height = (start-end) * self.bf
                        
            self.d.append(draw.Rectangle(x,y,width,height,fill=matplotlib.colors.to_hex(color, keep_alpha=True), opacity=1, stroke="black", sroke_width=2))            
            if color == "black":
                self.d.append(draw.Text(name, text_size, 0,0, transform=f"translate({x},{y}),rotate({90})",  fill='white'))  
            else:
                self.d.append(draw.Text(name, text_size, 0,0, transform=f"translate({x},{y}),rotate({90})",  fill='black'))  

            y += height
        
    
    def add_time_scale(self):
        
        one_leaf = self.t.get_leaves()[0]
        y =   one_leaf.ycoor - (self.bf * 4600)
        x = -(self.width)/2 
        
        ts = Timescale()

        for index, row in ts.Periods[["Start","End","Name", "Color"]][::-1].iterrows():

            start = row["Start"]
            end =   row["End"]
            name =  row["Name"]
            color = row["Color"]
          
            width = 30
            height = (start-end) * self.bf
                        
            self.d.append(draw.Rectangle(x,y,width,height,fill=matplotlib.colors.to_hex(color, keep_alpha=True), opacity=1, stroke="black", sroke_width=1))            
            
            y += height
            
    def add_numbers(self,clade2color, text_size=12, x_adjust = 0, y_adjust = 0, rotation = 90, text_color="black"):
        i = 1
        for clade, _ in clade2color.items():
            self.d.append(draw.Text(f"{i}", text_size, 0, 0, transform=f"translate({clade.xcoor + x_adjust},{clade.ycoor + y_adjust}),rotate({rotation})", fill=text_color))
            i+=1

    def add_cis(self, clade2ci, color="blue", opacity = 0.8, stroke_width = 1):
        
        hpadding = self.params["hpadding"] 
        vpadding = self.params["vpadding"] 
        
        present = self.t.get_leaves()[0].ycoor
        start   = self.t.ycoor
        total_length_of_tree = self.t.get_distance(self.t.get_leaves()[0])
        
        for clade, ci in clade2ci.items():            
            ci_start, ci_end = ci                                   
            adj_ci_start = self.height/2 - vpadding/2 - (ci_start * (present - start)) / total_length_of_tree         
            adj_ci_end  = self.height/2 - vpadding/2 -  (ci_end   * (present - start)) / total_length_of_tree         
            self.d.append(draw.Line(clade.xcoor,adj_ci_start,clade.xcoor,adj_ci_end, fill="None", stroke_width=stroke_width, stroke=color, opacity = opacity ))    
                     
            
    def add_stripes(self, intervals):  
       
        one_leaf = self.t.get_leaves()[0]
        y = one_leaf.ycoor + (self.bf * 4600)
        x = -(self.width)/2 + 30
            
        for start, end in intervals:
            
            width = 30
            height = (start-end) * self.bf                    
            self.d.append(draw.Rectangle(x, y - (start*self.bf), self.width, height,fill="grey", opacity=0.2,))            
            
            
    def color_background(self, clade2bg, opacity = 0.5, gradient=False, gradient_stop=0.3, color_stem=False):
        
        yl = (self.t.get_leaves()[0]).ycoor
        
        for n, color in clade2bg.items():
            if n.is_leaf():
                continue
        
            x,y = n.xcoor, n.ycoor
            xs = [l.xcoor for l in n.get_leaves()]

            self.d.append(draw.Rectangle(min(xs), y , max(xs) - min(xs), yl - y ,fill=color, opacity=opacity, sroke_width=0))            
        

        

class NexusParser():
    def __init__(self, file):
                
        self.index2info = dict()
        
        n = NexusReader.from_file(file)
        
        tree = newick.loads(n.trees[0].split(" ")[-1])[0]
        tree.visit(lambda n: self.read_info(n.comment))
        tree.visit(lambda n: setattr(n, "name", self.get_index(n.comment)) if n.name == None else None)
        tree.visit(lambda n: n.comments.clear())
        
        self.t = ete3.Tree(newick.dumps(tree), format=1)
        
        
        
    def get_index(self, x):

        x = x.replace("&","")
        rawinfo = re.split(",(?=[^\}]*(?:\{|$))", x)

        for item in rawinfo:
            variable, value = item.split("=")

            if variable == "index":
                return value
                break

        
    def read_info(self, x):    
        x = x.replace("&","")
        rawinfo = re.split(",(?=[^\}]*(?:\{|$))", x)
        variable2value = dict()
        for item in rawinfo:
            variable, value = item.split("=")
            variable2value[variable] = value
        if variable2value["index"] in self.index2info:
            raise Exception("Index duplicated")
        else:
            self.index2info[variable2value["index"]] = variable2value
        return variable2value

    
    
def compute_reds(mtree):
    
    def get_average(node):
        dists = list()
        for l in node.get_leaves():
            mdist = l.get_distance(node.up)
            dists.append(mdist)
        return(float(sum(dists))/len(dists))
    

    for n in mtree.traverse():
        if n.is_root():
            n.add_feature("RED", 0.0)
            continue
        if n.is_leaf():
            n.add_feature("RED", 1)
            continue

        n.add_feature("RED", 0.0)

        u = get_average(n)
        n.RED = n.up.RED + ((n.dist / u) * (1 - n.up.RED))

    for n in mtree.traverse():
        if n.is_root():
            continue
        n.dist = n.RED - n.up.RED



    
            
def get_node_order(mytree):
    
    distances = dict()

    for mynode in mytree.traverse():
       if mynode.is_leaf():
           continue
       one_leaf = mynode.get_leaves()[0]
       dist = mynode.get_distance(one_leaf)
       distances[mynode.name] = dist

    node_order = sorted(distances.items(), key=lambda x: x[1])
    node_order = [x[0] for x in node_order][::-1]
    return ",".join(node_order)


def map_trees(t,t2):

    for n in t.traverse():    
        if not n.is_leaf():
            c1, c2 = n.get_children()
            l1 = c1.get_leaves()[0]
            l2 = c2.get_leaves()[0]
            
            if l1.name not in t2 or l2.name not in t2:
                continue
            
            t_l1 = t2&(l1.name)
            t_l2 = t2&(l2.name)


            n2 = t2.get_common_ancestor(t_l1, t_l2)
            n.name = n2.name


def get_advanced_mapping(t,t2, ignore_leaves = {}):
    
    temp_map = dict()
    
    mapping = dict()
    
    for n in t.traverse():
        leaves = "-".join(sorted(([x.name for x in n.get_leaves() if x.name not in ignore_leaves])))
        temp_map[leaves] = n.name
        
    for n in t2.traverse():
        leaves = "-".join(sorted([x.name for x in n.get_leaves()  if x.name not in ignore_leaves])) 
        if leaves in temp_map:        
            mapping[n.name] = temp_map[leaves]
        
    return mapping   
    
    
            
def get_tree_mapping(t,t2):
    
    flag = False
    
    mapping = dict()

    for n in t.traverse(): 
        
        if not n.is_leaf():
            c1, c2 = n.get_children()
            l1 = c1.get_leaves()[0]
            l2 = c2.get_leaves()[0]
            
            if l1.name not in t2 or l2.name not in t2:
                flag = True
                continue
            else:
                
                t_l1 = t2&(l1.name)
                t_l2 = t2&(l2.name)
                        
            n2 = t2.get_common_ancestor(t_l1, t_l2)
            mapping[n2.name] = n.name
        else:
            mapping[n.name] = n.name
    if flag:
        print("Not all nodes were mapped, the trees are probably different")
    return mapping


def get_phyla_clade2bg(t):

    for n in t.traverse("postorder"):    
        if n.is_leaf():
            phylum = ''.join([i for i in n.name if not i.isdigit()])
            n.add_feature("phyla",  set() )
            (n.phyla).add(phylum)
        else:
            c1, c2 = n.get_children()
            n.add_feature("phyla", c1.phyla.union(c2.phyla))        

def get_phylum2node(t):
    phylum2node = dict()
    for n in t.traverse():
        if len(n.phyla) >= 2:
            continue
        else:
            phylum = list(n.phyla)[0]
            
            if phylum not in phylum2node:
                phylum2node[phylum] = n
            else:
                if len(n) > len(phylum2node[phylum]):
                    phylum2node[phylum] = n
    return phylum2node


def fasta_parser(myfile):
    with open(myfile) as f:

        header = ""
        seq = ""
        for line in f:
            if line[0] == ">":
                if seq != "":
                    yield (header[1:], seq)
                    header = line.strip()
                    seq = ""
                else:
                    header = line.strip()
            else:
                seq += line.strip()
        yield (header[1:], seq)

