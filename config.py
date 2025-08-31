"""
VolatiQ Configuration Management
Handles environment variables and application settings
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration class"""
    
    # Flask Configuration
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # API Configuration
    API_HOST: str = os.getenv('API_HOST', '127.0.0.1')
    API_PORT: int = int(os.getenv('API_PORT', '5000'))
    API_URL: str = os.getenv('API_URL', 'http://localhost:5000')
    
    # Dashboard Configuration
    DASH_HOST: str = os.getenv('DASH_HOST', '127.0.0.1')
    DASH_PORT: int = int(os.getenv('DASH_PORT', '8050'))
    
    # Model Configuration
    MODEL_PATH: str = os.getenv('MODEL_PATH', 'model/saved_model/volatility_model.keras')
    SCALER_PATH: str = os.getenv('SCALER_PATH', 'model/saved_model/scaler.save')
    MAX_PREDICTION_BATCH_SIZE: int = int(os.getenv('MAX_PREDICTION_BATCH_SIZE', '1000'))
    MODEL_RETRAIN_INTERVAL: int = int(os.getenv('MODEL_RETRAIN_INTERVAL', '86400'))
    
    # Database Configuration
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'volatiq')
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'volatiq')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'changeme')
    
    # Redis Configuration
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv('ALPHA_VANTAGE_API_KEY')
    YAHOO_FINANCE_API_KEY: Optional[str] = os.getenv('YAHOO_FINANCE_API_KEY')
    
    # Security
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    DATADOG_API_KEY: Optional[str] = os.getenv('DATADOG_API_KEY')
    
    # Cloud Storage
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET: Optional[str] = os.getenv('AWS_S3_BUCKET')
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.FLASK_ENV == 'development'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.FLASK_ENV == 'production'
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if self.is_production:
            if self.SECRET_KEY == 'dev-key-change-in-production':
                errors.append("SECRET_KEY must be changed in production")
            
            if self.JWT_SECRET_KEY == 'jwt-secret-change-in-production':
                errors.append("JWT_SECRET_KEY must be changed in production")
                
            if not self.MODEL_PATH or not os.path.exists(self.MODEL_PATH):
                errors.append(f"Model file not found: {self.MODEL_PATH}")
                
            if not self.SCALER_PATH or not os.path.exists(self.SCALER_PATH):
                errors.append(f"Scaler file not found: {self.SCALER_PATH}")
        
        return errors


# Global configuration instance
config = Config()
