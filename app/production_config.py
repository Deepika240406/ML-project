"""
Production Configuration Management
Centralized configuration for production environment with security and validation.
"""
import os
import warnings
import logging
import logging.handlers
from pathlib import Path
from urllib.parse import quote_plus
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ProductionConfig:
    """Production configuration with environment variable validation"""
    
    def __init__(self):
        self._load_configuration()
        self._validate_configuration()
        self._setup_logging()
    
    def _get_api_key(self):
        """Get OpenRouter API key from multiple sources safely"""
        env_key = os.getenv('OPENROUTER_API_KEY', '')
        if env_key and env_key.strip() and env_key != 'your_openrouter_api_key_here':
            return env_key.strip()

        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                try:
                    sec_key = st.secrets.get('OPENROUTER_API_KEY', '')
                    if sec_key and str(sec_key).strip():
                        return str(sec_key).strip()
                except Exception:
                    pass
        except Exception:
            pass

        return ''

    def _load_configuration(self):
        """Load all configuration from environment variables with defaults"""
        
        # Application Configuration
        self.APP_NAME = os.getenv('APP_NAME', 'AI Real Estate Valuation System')
        self.VERSION = os.getenv('VERSION', '2.0.0')
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        self.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Database Configuration
        self.DATABASE_CONFIG = {
            'url': os.getenv('DATABASE_URL', ''),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'name': os.getenv('DB_NAME', 'real_estate_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            'connection_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
        }
        
        # AI Configuration
        self.AI_CONFIG = {
            'enable_gemini_ai': os.getenv('ENABLE_GEMINI_AI', 'true').lower() == 'true',
            'gemini_api_key': self._get_api_key(),
            'request_timeout': int(os.getenv('AI_REQUEST_TIMEOUT', '30')),
            'max_retries': int(os.getenv('AI_MAX_RETRIES', '3'))
        }
        
        # Security Configuration
        self.SECURITY_CONFIG = {
            'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'rate_limit_requests_per_minute': int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '60')),
            'rate_limit_predictions_per_hour': int(os.getenv('RATE_LIMIT_PREDICTIONS_PER_HOUR', '100')),
            'max_upload_size_mb': int(os.getenv('MAX_UPLOAD_SIZE_MB', '10')),
            'session_timeout_minutes': int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
        }
        
        # Logging Configuration
        self.LOGGING_CONFIG = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file_path': os.getenv('LOG_FILE_PATH', 'logs/production.log'),
            'max_file_size_mb': int(os.getenv('LOG_MAX_FILE_SIZE_MB', '10')),
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            'enable_performance_monitoring': os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        }
        
        # Cache Configuration
        self.CACHE_CONFIG = {
            'redis_url': os.getenv('REDIS_URL', ''),
            'ttl_seconds': int(os.getenv('CACHE_TTL_SECONDS', '3600')),
            'max_memory_cache_size': int(os.getenv('MAX_MEMORY_CACHE_SIZE', '100'))
        }
        
        # Data Configuration
        self.DATA_CONFIG = {
            'min_area': max(int(os.getenv('MIN_PROPERTY_AREA', '100')), 50),  # Ensure minimum is at least 50
            'max_area': max(int(os.getenv('MAX_PROPERTY_AREA', '10000')), 1000),  # Ensure maximum is at least 1000
            'min_bhk': max(int(os.getenv('MIN_BHK', '1')), 1),  # Ensure minimum is at least 1
            'max_bhk': max(int(os.getenv('MAX_BHK', '10')), 2),  # Ensure maximum is at least 2
            'min_price': int(os.getenv('MIN_PRICE', '100000')),
            'max_price': int(os.getenv('MAX_PRICE', '1000000000'))
        }
        
        # Ensure valid ranges
        if self.DATA_CONFIG['min_area'] >= self.DATA_CONFIG['max_area']:
            self.DATA_CONFIG['max_area'] = self.DATA_CONFIG['min_area'] + 1000
        
        if self.DATA_CONFIG['min_bhk'] >= self.DATA_CONFIG['max_bhk']:
            self.DATA_CONFIG['max_bhk'] = self.DATA_CONFIG['min_bhk'] + 1
        
        # Price range sanity check
        if self.DATA_CONFIG['min_price'] >= self.DATA_CONFIG['max_price']:
            self.DATA_CONFIG['max_price'] = self.DATA_CONFIG['min_price'] * 10
        
        # External APIs
        self.EXTERNAL_APIS = {
            'weather_api_key': os.getenv('WEATHER_API_KEY', ''),
            'maps_api_key': os.getenv('MAPS_API_KEY', ''),
            'sentry_dsn': os.getenv('SENTRY_DSN', ''),
            'google_analytics_id': os.getenv('GOOGLE_ANALYTICS_ID', '')
        }
        
        # Performance Configuration
        self.PERFORMANCE_CONFIG = {
            'max_concurrent_requests': int(os.getenv('MAX_CONCURRENT_REQUESTS', '100')),
            'request_timeout_seconds': int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30')),
            'enable_caching': os.getenv('ENABLE_CACHING', 'true').lower() == 'true',
            'cache_expiry_hours': int(os.getenv('CACHE_EXPIRY_HOURS', '24'))
        }
        
        # Monitoring Configuration
        self.MONITORING_CONFIG = {
            'enable_metrics': os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
            'metrics_interval_seconds': int(os.getenv('METRICS_INTERVAL_SECONDS', '60')),
            'health_check_interval_seconds': int(os.getenv('HEALTH_CHECK_INTERVAL_SECONDS', '30'))
        }
        
        # Rate Limiting (for backward compatibility)
        self.RATE_LIMIT = {
            'predictions_per_hour': self.SECURITY_CONFIG['rate_limit_predictions_per_hour'],
            'api_calls_per_minute': self.SECURITY_CONFIG['rate_limit_requests_per_minute']
        }
        
        # Streamlit Configuration (for backward compatibility)
        self.STREAMLIT_CONFIG = {
            'page_title': f"{self.APP_NAME} v{self.VERSION}",
            'page_icon': "🏠",
            'layout': "wide",
            'initial_sidebar_state': "expanded"
        }
    
    def _validate_configuration(self):
        """Validate critical configuration values"""
        
        # Check environment
        valid_environments = ['development', 'staging', 'production']
        if self.ENVIRONMENT not in valid_environments:
            raise ValueError(f"Invalid environment: {self.ENVIRONMENT}. Must be one of {valid_environments}")
        
        # Production environment checks
        if self.ENVIRONMENT == 'production':
            if self.DEBUG:
                warning = "Debug mode is enabled in production environment"
                warnings.warn(warning, UserWarning)
            
            if self.SECURITY_CONFIG['secret_key'] == 'dev-secret-key-change-in-production':
                raise ValueError("Production secret key not configured")
            
            if not self.AI_CONFIG['gemini_api_key'] and self.AI_CONFIG['enable_gemini_ai']:
                warnings.warn("Gemini AI is enabled but API key is not configured", UserWarning)
        
        # Note: DATA_CONFIG ranges are auto-corrected during loading, no validation needed
        
        # Validate rate limits if SECURITY_CONFIG exists
        if hasattr(self, 'SECURITY_CONFIG'):
            if self.SECURITY_CONFIG['rate_limit_requests_per_minute'] <= 0:
                raise ValueError("Rate limit must be positive")
            
            if self.SECURITY_CONFIG['rate_limit_predictions_per_hour'] <= 0:
                raise ValueError("Prediction rate limit must be positive")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        
        # Create logs directory if it doesn't exist
        log_path = Path(self.LOGGING_CONFIG['file_path'])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging level
        log_level = getattr(logging, self.LOGGING_CONFIG['level'].upper(), logging.INFO)
        
        # Basic logging configuration
        log_path = Path(self.LOGGING_CONFIG['file_path'])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        max_bytes = self.LOGGING_CONFIG['max_file_size_mb'] * 1024 * 1024
        rotating_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=self.LOGGING_CONFIG['backup_count'],
            encoding='utf-8'
        )
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                rotating_handler,
                logging.StreamHandler()
            ]
        )
    
    def get_database_url(self) -> str:
        """Get complete database URL with URL-encoded credentials"""
        if self.DATABASE_CONFIG['url']:
            return self.DATABASE_CONFIG['url']
        
        # Build URL from components with URL-encoded credentials
        user = quote_plus(self.DATABASE_CONFIG['user'])
        password = quote_plus(self.DATABASE_CONFIG['password'])
        return (f"postgresql://{user}:"
                f"{password}@"
                f"{self.DATABASE_CONFIG['host']}:"
                f"{self.DATABASE_CONFIG['port']}/"
                f"{self.DATABASE_CONFIG['name']}")
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == 'development'
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without sensitive data)"""
        return {
            'app_name': self.APP_NAME,
            'version': self.VERSION,
            'environment': self.ENVIRONMENT,
            'debug': self.DEBUG,
            'ai_enabled': self.AI_CONFIG['enable_gemini_ai'],
            'caching_enabled': self.PERFORMANCE_CONFIG['enable_caching'],
            'monitoring_enabled': self.MONITORING_CONFIG['enable_metrics'],
            'database_configured': bool(self.DATABASE_CONFIG['url'] or self.DATABASE_CONFIG['password']),
            'redis_configured': bool(self.CACHE_CONFIG['redis_url'])
        }
    
    def setup_logging(self):
        """Setup comprehensive logging for production"""
        self._setup_logging()

# Global configuration instance
config = ProductionConfig()

# Export commonly used configurations for backward compatibility
VERSION = config.VERSION
DEBUG = config.DEBUG
ENVIRONMENT = config.ENVIRONMENT
