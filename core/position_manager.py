import time

class PrintPositionManager:
    def __init__(self):
        self.grid_size = (10, 10)  # 10x10 grid
        self.square_size = 10      # 10mm square
        self.gap = 5              # 5mm gap
        self.start_pos = (32.4, 145)  # start position (from gcode file)
        self.print_history = {}    # record printed positions
        
    def get_next_position(self):
        """Get next available print position"""
        for row in range(self.grid_size[0]):
            for col in range(self.grid_size[1]):
                pos_id = f"square_{row}_{col}"
                if pos_id not in self.print_history:
                    x = self.start_pos[0] + col * (self.square_size + self.gap)
                    y = self.start_pos[1] - row * (self.square_size + self.gap)
                    return {
                        'id': pos_id,
                        'position': (x, y),
                        'index': row * self.grid_size[1] + col
                    }
        return None
    
    def mark_position_printed(self, pos_id, params):
        """Mark position as printed, record parameters"""
        self.print_history[pos_id] = {
            'timestamp': time.strftime("%Y%m%d_%H%M%S"),
            'parameters': params
        } 
