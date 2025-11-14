"""Entropy and UUID detection for safety guards."""

import re
import math
from collections import Counter
from typing import List


def calculate_entropy(s: str) -> float:
    """
    Calculate Shannon entropy: -sum(p * log2(p))
    High entropy = random/unpredictable
    
    Args:
        s: String to analyze
    
    Returns:
        Entropy value (0-8 for base64, typically 3.5+ for random)
    """
    if not s:
        return 0
    
    counts = Counter(s)
    length = len(s)
    
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    
    return entropy


def is_random_identifier(segment: str, entropy_threshold: float = 3.5) -> bool:
    """
    Detect UUIDs, hashes, and random identifiers in URL segments.
    
    Examples that should be detected:
    - /docs/8f4a3b2c-1d6e-4f9a-b3c2-7e8d9f0a1b2c/page
    - /article/aB3dE7fG9hJ2kL4mN6pQ8rS
    - /files/a1b2c3d4e5f6g7h8i9j0
    
    Args:
        segment: URL path segment to check
        entropy_threshold: Minimum entropy to consider random (default: 3.5)
    
    Returns:
        True if segment appears to be a random identifier
    """
    # UUID pattern (with or without dashes)
    uuid_pattern = r'^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}$'
    if re.match(uuid_pattern, segment, re.IGNORECASE):
        return True
    
    # Long alphanumeric strings (20+ chars)
    if len(segment) >= 20 and segment.isalnum():
        # Calculate Shannon entropy
        entropy = calculate_entropy(segment)
        if entropy > entropy_threshold:
            return True
    
    return False


def check_url_for_random_segments(url: str, entropy_threshold: float = 3.5) -> tuple[bool, List[str]]:
    """
    Check URL path for random identifier segments.
    
    Args:
        url: URL to check
        entropy_threshold: Entropy threshold
    
    Returns:
        Tuple of (has_random_segments, list_of_suspicious_segments)
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    path_segments = [seg for seg in parsed.path.split('/') if seg]
    
    suspicious = []
    for segment in path_segments:
        if is_random_identifier(segment, entropy_threshold):
            suspicious.append(segment)
    
    return len(suspicious) > 0, suspicious
