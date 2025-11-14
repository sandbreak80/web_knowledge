"""StevenBlack hosts blocklist integration."""

from pathlib import Path
from typing import Set, Optional
import logging

logger = logging.getLogger(__name__)

# Cache for loaded blocklist
_blocklist_cache: Optional[Set[str]] = None


def load_blocklist(blocklist_path: str) -> Set[str]:
    """
    Load StevenBlack hosts blocklist from file.
    
    Args:
        blocklist_path: Path to blocklist file
    
    Returns:
        Set of blocked domains
    """
    global _blocklist_cache
    
    # Use cache if available
    if _blocklist_cache is not None:
        return _blocklist_cache
    
    blocklist: Set[str] = set()
    path = Path(blocklist_path)
    
    if not path.exists():
        logger.warning(f"Blocklist file not found: {blocklist_path}")
        return blocklist
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Extract domain (format: 0.0.0.0 domain.com)
                parts = line.split()
                if len(parts) >= 2:
                    domain = parts[1].lower()
                    blocklist.add(domain)
        
        _blocklist_cache = blocklist
        logger.info(f"Loaded {len(blocklist)} domains from blocklist")
        
    except Exception as e:
        logger.error(f"Failed to load blocklist: {e}")
    
    return blocklist


def check_blocklist(domain: str, blocklist_path: str) -> bool:
    """
    Check domain against StevenBlack hosts blocklist.
    
    Args:
        domain: Domain to check
        blocklist_path: Path to blocklist file
    
    Returns:
        True if domain is blocked, False otherwise
    """
    blocklist = load_blocklist(blocklist_path)
    
    if not blocklist:
        return False
    
    domain_lower = domain.lower()
    
    # Check exact match
    if domain_lower in blocklist:
        return True
    
    # Check www variant
    if domain_lower.startswith('www.'):
        if domain_lower[4:] in blocklist:
            return True
    else:
        if f"www.{domain_lower}" in blocklist:
            return True
    
    return False


def reset_blocklist_cache():
    """Reset blocklist cache (useful for testing)."""
    global _blocklist_cache
    _blocklist_cache = None
