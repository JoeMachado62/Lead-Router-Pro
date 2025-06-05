import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the lead router application"""
    
    # GHL API Configuration
    GHL_API_KEY = os.getenv('GHL_API_KEY', os.getenv('GHL-API_KEY', ''))  # Support both formats
    GHL_PRIVATE_TOKEN = os.getenv('GHL_PRIVATE_TOKEN', 'pit-c361d89c-d943-4812-9839-8e3223c2f31a')
    GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID', 'ilmrtA1Vk6rvcy4BswKg')
    
    # GHL Agency API Key (required for user creation)
    GHL_AGENCY_API_KEY = os.getenv('GHL_AGENCY_API_KEY', '')
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 3000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Pipeline Configuration (you'll need to get these from GHL)
    PIPELINE_ID = os.getenv('PIPELINE_ID', 'marine_services')
    NEW_LEAD_STAGE_ID = os.getenv('NEW_LEAD_STAGE_ID', 'new_lead_stage_id')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    
    # Webhook Security (optional)
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            ('GHL_PRIVATE_TOKEN', cls.GHL_PRIVATE_TOKEN),
            ('GHL_LOCATION_ID', cls.GHL_LOCATION_ID)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value or var_value.startswith('your_'):
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
        
        return True

# Development configuration
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# Production configuration  
class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'INFO'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
