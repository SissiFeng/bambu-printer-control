from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import shutil
import os
import time
from typing import Dict, Any

Base = declarative_base()

class PrintJob(Base):
    __tablename__ = 'print_jobs'
    
    id = Column(Integer, primary_key=True)
    square_id = Column(String)  # like "square_0_0"
    print_timestamp = Column(DateTime)  # print start time
    image_timestamp = Column(DateTime)  # image capture time
    position_x = Column(Float)
    position_y = Column(Float)
    nozzle_temp = Column(Float)
    bed_temp = Column(Float)
    print_speed = Column(Float)
    status = Column(String)  # "printing", "completed", "failed"
    image_url = Column(String)  # S3 image URL

    def match_image(self, image_url: str, image_timestamp: datetime):
        """Match print job and image"""
        self.image_url = image_url
        self.image_timestamp = image_timestamp
        # calculate time difference for verification
        time_diff = abs((image_timestamp - self.print_timestamp).total_seconds())
        return time_diff < 300  # 5 minutes are considered a match

class DatabaseManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config['path']
        self.backup_dir = config.get('backup_dir', 'backups')
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize database
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Setup backup schedule
        self.backup_interval = config.get('backup_interval', 24 * 60 * 60)  # 24 hours
        self.last_backup = self._get_last_backup_time()
        
    def create_backup(self) -> str:
        """Create a backup of the database
        
        Returns:
            str: Path to backup file
        """
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(
                self.backup_dir,
                f'print_history_{timestamp}.db'
            )
            
            # Create backup
            shutil.copy2(self.db_path, backup_path)
            
            # Update last backup time
            self.last_backup = time.time()
            
            self.logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
            
    def check_backup_needed(self) -> bool:
        """Check if backup is needed based on interval
        
        Returns:
            bool: True if backup is needed
        """
        return (time.time() - self.last_backup) >= self.backup_interval
        
    def _get_last_backup_time(self) -> float:
        """Get last backup time from existing backups
        
        Returns:
            float: Timestamp of last backup
        """
        try:
            backups = os.listdir(self.backup_dir)
            if not backups:
                return 0
                
            # Get most recent backup time
            latest = max(
                os.path.getmtime(os.path.join(self.backup_dir, f))
                for f in backups
            )
            return latest
            
        except Exception:
            return 0
            
    def cleanup_old_backups(self, keep_days: int = 30):
        """Remove backups older than specified days"""
        try:
            cutoff = time.time() - (keep_days * 24 * 60 * 60)
            
            for backup in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup)
                if os.path.getmtime(backup_path) < cutoff:
                    os.remove(backup_path)
                    self.logger.info(f"Removed old backup: {backup}")
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup backups: {e}") 
