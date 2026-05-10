import math

class Palletizer:
    def __init__(self, spacing_cm=6.0, grid_size=3):
        self.spacing = spacing_cm / 100.0  
        self.grid_size = grid_size
        self.counts = {}

    def get_grid_offsets(self, key):
        """Returns raw (reach_offset, lateral_offset) in meters."""
        if key not in self.counts: 
            self.counts[key] = 0
            
        idx = self.counts[key] % (self.grid_size ** 2)
        row = idx // self.grid_size  
        col = idx % self.grid_size   
        
        dr = (row - (self.grid_size // 2)) * self.spacing
        dl = (col - (self.grid_size // 2)) * self.spacing
        
        self.counts[key] += 1
        return dr, dl