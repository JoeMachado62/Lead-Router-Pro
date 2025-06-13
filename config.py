import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This should be the first thing that runs when the module is imported.
load_dotenv()

class Config:
    """Base configuration class. Contains settings common to all environments."""
    
    # --- CRITICAL GHL API Credentials ---
    # We fetch directly from the environment. No default fallbacks for these.
    GHL_LOCATION_API = os.getenv('GHL_LOCATION_API')  # V1 Location API Key
    GHL_PRIVATE_TOKEN = os.getenv('GHL_PRIVATE_TOKEN')  # V2 PIT Token (fallback)
    GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID')
    GHL_AGENCY_API_KEY = os.getenv('GHL_AGENCY_API_KEY') # Optional, for user creation
    
    # --- Pipeline Configuration (Essential for creating Opportunities) ---
    # These should be defined in your .env file for the specific pipeline you use.
    PIPELINE_ID = os.getenv('PIPELINE_ID')
    NEW_LEAD_STAGE_ID = os.getenv('NEW_LEAD_STAGE_ID')

    # --- Application Settings ---
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    
    # --- Other Settings ---
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '') # Optional, for security

    @classmethod
    def validate_critical_config(cls):
        """
        Validates that essential configuration variables are set.
        This should be called at application startup.
        """
        # A dictionary of variable names and their loaded values
        required_vars = {
            'GHL_PRIVATE_TOKEN': cls.GHL_PRIVATE_TOKEN,
            'GHL_LOCATION_ID': cls.GHL_LOCATION_ID,
            'PIPELINE_ID': cls.PIPELINE_ID,
            'NEW_LEAD_STAGE_ID': cls.NEW_LEAD_STAGE_ID,
        }
        
        missing_vars = [name for name, value in required_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(f"FATAL ERROR: Missing required environment variables: {', '.join(missing_vars)}. Please set them in your .env file.")
        
        print("✅ Critical configuration validated successfully.")


class DevelopmentConfig(Config):
    """Configuration for the development environment."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Configuration for the production environment."""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    # In production, you might want a stricter rate limit
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 45))


# --- Environment-based Config Selection ---
# Set an environment variable 'APP_ENV' to 'production' to use production settings
# Default is 'development'
APP_ENV = os.getenv('APP_ENV', 'development')

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}

# Get the final configuration object based on the environment
AppConfig = config_by_name.get(APP_ENV, DevelopmentConfig)

# --- Immediate Validation at Startup ---
# We call the validation method here to ensure the app fails fast if misconfigured.
try:
    AppConfig.validate_critical_config()
except ValueError as e:
    # Print the error clearly and exit if validation fails
    print(f"\n--- CONFIGURATION ERROR ---\n{e}\n---------------------------\n")
    # In a real app, you might want to sys.exit(1) here
    raise
