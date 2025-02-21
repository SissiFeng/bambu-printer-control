import yaml
import os

class PrinterController:
    def __init__(self, config_path=None):
        # 加载配置
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/printer_config.yaml'
            )
            
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # 初始化组件
        self.position_manager = PrintPositionManager(
            self.config['grid']
        )
        self.gcode_generator = GCodeGenerator(
            self.config['print']
        )
        self.db_manager = DatabaseManager(
            self.config['database']
        )
        
        # 连接打印机
        self.connect(
            self.config['printer']['ip'],
            self.config['printer']['access_code'],
            self.config['printer']['serial']
        )
        
    def connect(self, ip, access_code, serial):
        """连接打印机"""
        self.printer = bl.Printer(ip, access_code, serial)
        self.printer.connect()
        
    def print_next_square(self, params):
        """打印下一个方块"""
        # 获取下一个位置
        next_pos = self.position_manager.get_next_position()
        if not next_pos:
            return "No available positions"
            
        # 生成G-code
        gcode = self.gcode_generator.generate_square_gcode(next_pos, params)
        
        # 创建3mf文件
        filename = f"square_{next_pos['id']}.3mf"
        gcode_location = "Metadata/plate_1.gcode"
        io_file = create_zip_archive_in_memory(gcode, gcode_location)
        
        # 上传并打印
        result = self.printer.upload_file(io_file, filename)
        if "226" in result:
            self.printer.start_print(filename, 1)
            # 记录打印位置
            self.position_manager.mark_position_printed(next_pos['id'], params)
            return f"Started printing square {next_pos['id']}"
        else:
            return "Error uploading file" 
