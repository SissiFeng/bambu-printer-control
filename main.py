import os
import yaml
import logging.config
import time
from core.printer_controller import PrinterController
from core.mqtt_handler import MQTTHandler

def setup_logging():
    """Setup logging configuration"""
    config_path = os.path.join(
        os.path.dirname(__file__),
        'config/logging_config.yaml'
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)

def load_config():
    """Load configuration from yaml file"""
    config_path = os.path.join(
        os.path.dirname(__file__),
        'config/printer_config.yaml'
    )
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

class PrinterSystem:
    """Main printer system class"""
    
    def __init__(self):
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger('printer')
        
        # Load configuration
        self.config = load_config()
        self.logger.info("Configuration loaded successfully")
        
        # Initialize components
        self._init_components()
        
    def _init_components(self):
        """Initialize system components"""
        try:
            # Initialize printer controller
            self.printer = PrinterController(self.config)
            if not self.printer.connect():
                raise Exception("Failed to connect to printer")
            
            # Initialize MQTT handler
            self.mqtt_handler = MQTTHandler(self.config['mqtt'], self.printer)
            self.mqtt_handler.connect()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
            
    def run(self):
        """Main system loop"""
        self.logger.info("System initialized, entering main loop")
        
        while True:
            try:
                # Check printer connection
                if not self.printer.check_connection():
                    self.logger.error("Lost connection to printer")
                    continue
                
                # Check if backup needed
                if self.printer.db_manager.check_backup_needed():
                    self.printer.db_manager.create_backup()
                    self.printer.db_manager.cleanup_old_backups()
                
                # Get printer status
                status = self.printer.get_status()
                
                # Publish status
                self.mqtt_handler.publish_status(status)
                
                # Sleep for a bit
                time.sleep(5)
                
            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Wait before retrying

def main():
    try:
        system = PrinterSystem()
        system.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 
