class GCodeGenerator:
    def __init__(self):
        self.template_path = "template/10x10 0.1.gcode"
        with open(self.template_path, 'r') as f:
            self.template = f.read()
    
    def generate_square_gcode(self, position, params):
        """Generate G-code for a single square
        
        Args:
            position (dict): position information
            params (dict): print parameters
        """
        gcode = self.template
        
        # replace position parameters
        x, y = position['position']
        gcode = gcode.replace("X42.15", f"X{x}")
        gcode = gcode.replace("Y154.75", f"Y{y}")
        
        # replace print parameters
        gcode = gcode.replace("[nozzle_temperature]", str(params['nozzle_temp']))
        gcode = gcode.replace("[bed_temperature]", str(params['bed_temp']))
        
        return gcode 
