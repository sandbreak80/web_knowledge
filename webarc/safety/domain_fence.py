"""Domain fencing and validation utilities."""

from urllib.parse import urlparse
from typing import Optional
import publicsuffix2


def extract_registered_domain(domain: str) -> str:
    """
    Extract registered domain (e.g., "example.com" from "sub.example.com").
    
    Uses publicsuffix2 to handle TLDs correctly.
    
    Args:
        domain: Domain name
    
    Returns:
        Registered domain name
    """
    try:
        return publicsuffix2.get_sld(domain)
    except Exception:
        # Fallback: return domain as-is if parsing fails
        return domain


def is_same_registered_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs belong to the same registered domain.
    
    Args:
        url1: First URL
        url2: Second URL
    
    Returns:
        True if same registered domain
    """
    domain1 = extract_domain_from_url(url1)
    domain2 = extract_domain_from_url(url2)
    
    reg_domain1 = extract_registered_domain(domain1)
    reg_domain2 = extract_registered_domain(domain2)
    
    return reg_domain1 == reg_domain2


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
    
    Returns:
        Domain name
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove port if present
    if ':' in domain:
        domain = domain.split(':')[0]
    
    return domain


def validate_domain_restriction(
    url: str,
    allowed_domain: Optional[str] = None,
    allowed_prefix: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    Validate if URL matches domain and prefix restrictions.
    
    Args:
        url: URL to validate
        allowed_domain: Required domain (if specified)
        allowed_prefix: Required URL path prefix (if specified)
    
    Returns:
        Tuple of (is_allowed, reason_if_not)
    """
    if allowed_domain:
        url_domain = extract_domain_from_url(url)
        allowed_domain_lower = allowed_domain.lower()
        
        # Check exact match or subdomain
        if url_domain != allowed_domain_lower and not url_domain.endswith('.' + allowed_domain_lower):
            return False, f"Domain mismatch: {url_domain} not in {allowed_domain}"
    
    if allowed_prefix:
        parsed = urlparse(url)
        path = parsed.path
        
        if not path.startswith(allowed_prefix):
            return False, f"Path prefix mismatch: {path} does not start with {allowed_prefix}"
    
    return True, None
