import time

class PrintPositionManager:
    def __init__(self):
        self.grid_size = (10, 10)  # 10x10 网格
        self.square_size = 10      # 10mm 方块
        self.gap = 5              # 5mm 间距
        self.start_pos = (32.4, 145)  # 起始位置(从gcode文件看到的)
        self.print_history = {}    # 记录已打印位置
        
    def get_next_position(self):
        """获取下一个可用的打印位置"""
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
        """标记位置已打印，记录参数"""
        self.print_history[pos_id] = {
            'timestamp': time.strftime("%Y%m%d_%H%M%S"),
            'parameters': params
        } 
