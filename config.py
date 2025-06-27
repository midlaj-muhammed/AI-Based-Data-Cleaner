import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 50))
    SUPPORTED_FORMATS = os.getenv('SUPPORTED_FORMATS', 'csv,xlsx,xls').split(',')
    
    # Application Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # AI Model Configuration
    OPENAI_MODEL = "gpt-3.5-turbo"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.3
    
    # Data Processing Settings
    MAX_ROWS_FOR_AI_PROCESSING = 1000
    SAMPLE_SIZE_FOR_ANALYSIS = 100
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in your .env file.")
        
        return True
