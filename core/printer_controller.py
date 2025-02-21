import time
import logging
from typing import Dict, Any, Optional
from bambulabs_api import Printer
from .gcode_generator import GCodeGenerator
from .position_manager import PrintPositionManager
from .database import DatabaseManager

class PrinterController:
    """Controller for Bambu A1 Mini printer"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize printer controller
        
        Args:
            config: Printer configuration including:
                - ip: Printer IP address
                - access_code: Printer access code
                - serial: Printer serial number
        """
        self.config = config
        self.printer = None
        self.connected = False
        
        # Initialize components
        self.position_manager = PrintPositionManager(config['grid'])
        self.gcode_generator = GCodeGenerator()
        self.db_manager = DatabaseManager(config['database'])
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """Connect to printer
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.printer = Printer(
                self.config['ip'],
                self.config['access_code'],
                self.config['serial']
            )
            self.connected = self.printer.connect()
            if self.connected:
                self.logger.info("Successfully connected to printer")
            return self.connected
        except Exception as e:
            self.logger.error(f"Failed to connect to printer: {e}")
            return False
            
    def start_print(self, params: Dict[str, Any]) -> bool:
        """Start printing with given parameters
        
        Args:
            params: Print parameters including:
                - nozzle_temp: Nozzle temperature
                - bed_temp: Bed temperature
                - print_speed: Print speed
                - etc.
                
        Returns:
            bool: True if print started successfully
        """
        if not self.connected:
            self.logger.error("Cannot start print: Not connected")
            return False
            
        try:
            # Get next position
            position = self.position_manager.get_next_position()
            if not position:
                self.logger.error("No available print positions")
                return False
                
            # Generate G-code
            gcode = self.gcode_generator.generate_square_gcode(position, params)
            
            # Create 3MF file
            filename = f"square_{position['id']}.3mf"
            gcode_location = "Metadata/plate_1.gcode"
            io_file = self.gcode_generator.create_3mf_package(gcode, gcode_location)
            
            # Upload and start print
            result = self.printer.upload_file(io_file, filename)
            if "226" in result:  # Upload successful
                # Record print job
                self.db_manager.record_print_job(
                    square_id=position['id'],
                    position_x=position['x'],
                    position_y=position['y'],
                    params=params
                )
                
                # Start printing
                self.printer.start_print(filename, 1)
                self.logger.info(f"Started printing square {position['id']}")
                return True
            else:
                self.logger.error("Failed to upload file")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting print: {e}")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """Get current printer status
        
        Returns:
            dict: Printer status information
        """
        if not self.connected:
            return {'status': 'disconnected'}
            
        try:
            status = self.printer.get_state()
            temps = self.printer.get_temperatures()
            
            return {
                'status': status,
                'bed_temp': temps.get('bed', 0),
                'nozzle_temp': temps.get('nozzle', 0),
                'progress': self.printer.get_progress(),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'status': 'error', 'error': str(e)}

    def set_temperatures(self, nozzle_temp: float, bed_temp: float) -> bool:
        """Set printer temperatures
        
        Args:
            nozzle_temp: Target nozzle temperature
            bed_temp: Target bed temperature
        
        Returns:
            bool: True if temperatures set successfully
        """
        if not self.connected:
            return False
        
        try:
            self.printer.set_nozzle_temperature(nozzle_temp)
            self.printer.set_bed_temperature(bed_temp)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set temperatures: {e}")
            return False

    def reconnect(self, max_attempts: int = 5, delay: int = 10) -> bool:
        """Attempt to reconnect to printer
        
        Args:
            max_attempts: Maximum number of reconnection attempts
            delay: Delay between attempts in seconds
            
        Returns:
            bool: True if reconnection successful
        """
        self.logger.info("Starting reconnection attempt")
        
        for attempt in range(max_attempts):
            try:
                if self.connect():
                    self.logger.info("Reconnection successful")
                    return True
                
                self.logger.warning(
                    f"Reconnection attempt {attempt + 1}/{max_attempts} failed"
                )
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Reconnection error: {e}")
                time.sleep(delay)
        
        self.logger.error("All reconnection attempts failed")
        return False

    def check_connection(self) -> bool:
        """Check printer connection status and attempt reconnection if needed
        
        Returns:
            bool: True if connected
        """
        if self.connected:
            try:
                # Try to get status to verify connection
                _ = self.printer.get_state()
                return True
            except Exception:
                self.logger.warning("Lost connection to printer")
                self.connected = False
        
        # Attempt reconnection if disconnected
        return self.reconnect() 
