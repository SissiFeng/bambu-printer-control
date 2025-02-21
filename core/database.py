from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class PrintJob(Base):
    __tablename__ = 'print_jobs'
    
    id = Column(Integer, primary_key=True)
    square_id = Column(String)  # 如 "square_0_0"
    print_timestamp = Column(DateTime)  # 打印开始时间
    image_timestamp = Column(DateTime)  # 图片拍摄时间
    position_x = Column(Float)
    position_y = Column(Float)
    nozzle_temp = Column(Float)
    bed_temp = Column(Float)
    print_speed = Column(Float)
    status = Column(String)  # "printing", "completed", "failed"
    image_url = Column(String)  # S3 图片URL

    def match_image(self, image_url: str, image_timestamp: datetime):
        """匹配打印任务和图片"""
        self.image_url = image_url
        self.image_timestamp = image_timestamp
        # 计算时间差，用于验证匹配
        time_diff = abs((image_timestamp - self.print_timestamp).total_seconds())
        return time_diff < 300  # 5分钟内的认为是匹配的

class DatabaseManager:
    def __init__(self, config_path):
        # 可以使用SQLite（本地）或 PostgreSQL（远程）
        self.engine = create_engine('sqlite:///print_history.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session() 
