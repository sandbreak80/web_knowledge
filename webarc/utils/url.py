"""URL normalization and canonicalization utilities."""

import re
from urllib.parse import urlparse, parse_qs, urlencode, unquote
import idna


def canonicalize_url(url: str, preserve_anchors: bool = False) -> str:
    """
    Complete URL normalization for deduplication.
    
    Args:
        url: URL to canonicalize
        preserve_anchors: If True, keep URL fragments (#section)
    
    Returns:
        Canonicalized URL string
    """
    # 1. Parse URL
    parsed = urlparse(url)
    
    # 2. Normalize scheme and domain to lowercase
    scheme = parsed.scheme.lower()
    domain = parsed.netloc.lower()
    
    # 3. Remove default ports
    if ':80' in domain and scheme == 'http':
        domain = domain.replace(':80', '')
    if ':443' in domain and scheme == 'https':
        domain = domain.replace(':443', '')
    
    # 4. IDN normalization (punycode → UTF-8)
    try:
        if domain.startswith('xn--'):
            domain = idna.decode(domain)
    except Exception:
        # If IDN decode fails, keep original
        pass
    
    # 5. Path normalization
    path = parsed.path
    
    # Remove duplicate slashes: //path → /path
    path = re.sub(r'/+', '/', path)
    
    # Trailing slash normalization
    # If path is empty, add trailing slash for root
    if not path:
        path = '/'
    elif path.endswith('.html') or path.endswith('.htm'):
        path = path.rstrip('/')  # Remove trailing slash from files
    elif not path.endswith('/'):
        # Add trailing slash to directories (paths without file extensions)
        path = path + '/'
    
    # 6. Query parameter normalization
    if parsed.query:
        # Parse query string
        params = parse_qs(parsed.query, keep_blank_values=True)
        
        # Remove tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
            'fbclid', 'gclid', 'mc_cid', 'mc_eid', '_ga', '_gl', 'msclkid'
        }
        params = {k: v for k, v in params.items() if k not in tracking_params}
        
        # Sort parameters alphabetically
        sorted_params = sorted(params.items())
        query = urlencode(sorted_params, doseq=True)
    else:
        query = ''
    
    # 7. Remove URL fragments (unless preserve_anchors is True)
    fragment = '' if not preserve_anchors else parsed.fragment
    
    # 8. Decode percent-encoding for safe characters
    # Note: unquote doesn't support 'safe' parameter, decode manually if needed
    path = unquote(path)
    
    # 9. Reconstruct URL
    canonical = f"{scheme}://{domain}{path}"
    if query:
        canonical += f"?{query}"
    if fragment:
        canonical += f"#{fragment}"
    
    return canonical


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
    
    Returns:
        Domain name (e.g., "example.com")
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove port if present
    if ':' in domain:
        domain = domain.split(':')[0]
    
    return domain


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
    
    Returns:
        True if same domain, False otherwise
    """
    domain1 = extract_domain(url1)
    domain2 = extract_domain(url2)
    return domain1 == domain2


def is_internal_link(source_url: str, target_url: str) -> bool:
    """
    Check if target URL is internal (same domain) relative to source.
    
    Args:
        source_url: Source page URL
        target_url: Target link URL
    
    Returns:
        True if internal link, False otherwise
    """
    return is_same_domain(source_url, target_url)
