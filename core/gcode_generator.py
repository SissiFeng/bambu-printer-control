class GCodeGenerator:
    def __init__(self):
        self.template_path = "template/10x10 0.1.gcode"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
    
    def generate_square_gcode(self, position, params):
        """生成单个方块的G-code
        
        Args:
            position (dict): 位置信息
            params (dict): 打印参数
        """
        gcode = self.template
        
        # 替换位置参数
        x, y = position['position']
        gcode = gcode.replace("X42.15", f"X{x}")
        gcode = gcode.replace("Y154.75", f"Y{y}")
        
        # 替换打印参数
        gcode = gcode.replace("[nozzle_temperature]", str(params['nozzle_temp']))
        gcode = gcode.replace("[bed_temperature]", str(params['bed_temp']))
        
        return gcode 
