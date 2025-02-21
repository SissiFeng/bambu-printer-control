import paho.mqtt.client as mqtt
import json
import logging
import time
from typing import Dict, Any, Optional
from .printer_controller import PrinterController
from .position_manager import PrintPositionManager

class MQTTHandler:
    """Handle MQTT communication with HF Space"""
    
    def __init__(self, config: Dict[str, Any], printer: PrinterController):
        """Initialize MQTT handler
        
        Args:
            config: MQTT configuration
            printer: Printer controller instance
        """
        self.config = config
        self.printer = printer
        self.client = mqtt.Client()
        
        # Configure MQTT client
        self.client.username_pw_set(config['username'], config['password'])
        self.client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self.connected = False
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(
                self.config['host'],
                self.config['port'],
                keepalive=60
            )
            self.client.loop_start()
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
            
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to MQTT broker")
            
            # Subscribe to command topic
            command_topic = f"bambu_a1_mini/command/{self.config['printer_serial']}"
            self.client.subscribe(command_topic)
            self.logger.info(f"Subscribed to {command_topic}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker with code: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        self.logger.warning("Disconnected from MQTT broker")
        
        # Attempt to reconnect
        if rc != 0:
            self.logger.info("Attempting to reconnect...")
            time.sleep(5)
            self.connect()
            
    def on_message(self, client, userdata, message):
        """Handle incoming MQTT messages"""
        try:
            payload = json.loads(message.payload)
            command = payload.get('action')
            
            if command == 'print':
                # Get print parameters
                params = payload.get('parameters', {})
                
                # Start print job
                result = self.printer.start_print(params)
                
                # Send response
                self.publish_status({
                    'status': 'printing' if result else 'error',
                    'square_id': self.printer.current_position.get('id'),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.publish_status({
                'status': 'error',
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
    def publish_status(self, status: Dict[str, Any]):
        """Publish printer status
        
        Args:
            status: Status information to publish
        """
        if not self.connected:
            self.logger.warning("Cannot publish status: Not connected")
            return
            
        topic = f"bambu_a1_mini/status/{self.config['printer_serial']}"
        self.client.publish(topic, json.dumps(status))
        
    def publish_image(self, image_url: str, square_id: str):
        """Publish image URL
        
        Args:
            image_url: S3 URL of the captured image
            square_id: ID of the printed square
        """
        if not self.connected:
            self.logger.warning("Cannot publish image: Not connected")
            return
            
        topic = f"bambu_a1_mini/image/{self.config['printer_serial']}"
        message = {
            'image_url': image_url,
            'square_id': square_id,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.client.publish(topic, json.dumps(message)) 
