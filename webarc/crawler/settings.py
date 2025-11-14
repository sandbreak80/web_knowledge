"""Scrapy settings configuration for WebArc."""

from typing import Optional
from webarc.config.loader import load_config
from webarc.config.schema import WebArcConfig


def get_scrapy_settings(config: Optional[WebArcConfig] = None) -> dict:
    """
    Get Scrapy settings dictionary from WebArc config.
    
    Args:
        config: WebArc configuration (loads default if None)
    
    Returns:
        Dictionary of Scrapy settings
    """
    if config is None:
        config = load_config()
    
    settings = {
        # Basic settings
        'BOT_NAME': 'webarc',
        'USER_AGENT': config.crawler.user_agent,
        
        # Concurrency
        'CONCURRENT_REQUESTS': config.crawler.concurrent_requests,
        'CONCURRENT_REQUESTS_PER_DOMAIN': config.crawler.concurrent_requests_per_domain,
        'DOWNLOAD_DELAY': config.crawler.download_delay,
        'DOWNLOAD_TIMEOUT': config.crawler.download_timeout,
        
        # Auto-throttle
        'AUTOTHROTTLE_ENABLED': config.crawler.autothrottle_enabled,
        'AUTOTHROTTLE_START_DELAY': config.crawler.autothrottle_start_delay,
        'AUTOTHROTTLE_MAX_DELAY': config.crawler.autothrottle_max_delay,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': config.crawler.autothrottle_target_concurrency,
        
        # Memory management
        'MEMUSAGE_ENABLED': config.crawler.memusage_enabled,
        'MEMUSAGE_LIMIT_MB': config.crawler.memusage_limit_mb,
        'MEMUSAGE_WARNING_MB': config.crawler.memusage_warning_mb,
        
        # Response limits
        'DOWNLOAD_MAXSIZE': config.crawler.download_maxsize,
        'DOWNLOAD_WARNSIZE': config.crawler.download_warnsize,
        
        # Retry
        'RETRY_TIMES': config.crawler.retry_times,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        
        # Middlewares
        'DOWNLOADER_MIDDLEWARES': {
            'webarc.crawler.middlewares.DomainFenceMiddleware': 543,
            'webarc.crawler.middlewares.BlocklistMiddleware': 544,
            'webarc.crawler.middlewares.WebArcRobotsTxtMiddleware': 545,
        },
        
        # Pipelines
        'ITEM_PIPELINES': {
            'webarc.crawler.pipelines.DuplicateFilterPipeline': 300,
        },
        
        # Custom settings
        'WEBCARC_CONFIG': config,
        'ALLOWED_DOMAIN': config.allow_domain,
        'ALLOWED_PREFIX': config.allow_prefix,
        
        # Logging
        'LOG_LEVEL': config.logging.level,
    }
    
    return settings
