"""State manager for resumable crawls."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import orjson
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """
    Periodically save crawler state for resumability.
    """
    
    def __init__(self, output_dir: Path, checkpoint_interval: int = 100):
        """
        Initialize state manager.
        
        Args:
            output_dir: Output directory
            checkpoint_interval: Save state every N URLs
        """
        self.output_dir = Path(output_dir)
        self.resume_file = self.output_dir / 'resume.jsonl'
        self.checkpoint_interval = checkpoint_interval
        self.pages_since_checkpoint = 0
    
    def save_state(self, crawler_state: Dict[str, Any]):
        """
        Save current crawler state.
        
        Args:
            crawler_state: State dictionary
        """
        state_entry = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "seed_url": crawler_state.get('seed_url'),
            "config_hash": crawler_state.get('config_hash', ''),
            "pages_crawled": crawler_state.get('pages_crawled', 0),
            "pages_queued": len(crawler_state.get('queue', [])),
            "pages_failed": crawler_state.get('pages_failed', 0),
            "queue": list(crawler_state.get('queue', [])),
            "visited": list(crawler_state.get('visited', [])),
            "status": crawler_state.get('status', 'running')
        }
        
        # Write to file (overwrite)
        with open(self.resume_file, 'wb') as f:
            f.write(orjson.dumps(state_entry) + b'\n')
        
        logger.debug(f"Checkpoint saved: {crawler_state.get('pages_crawled', 0)} pages")
    
    def maybe_checkpoint(self, crawler_state: Dict[str, Any]):
        """
        Save state if checkpoint interval reached.
        
        Args:
            crawler_state: Current crawler state
        """
        self.pages_since_checkpoint += 1
        
        if self.pages_since_checkpoint >= self.checkpoint_interval:
            self.save_state(crawler_state)
            self.pages_since_checkpoint = 0
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load previous crawler state.
        
        Returns:
            State dictionary or None if not found
        """
        if not self.resume_file.exists():
            return None
        
        try:
            with open(self.resume_file, 'rb') as f:
                content = f.read()
                if content:
                    state = orjson.loads(content)
                    logger.info(f"Loaded checkpoint: {state.get('pages_crawled', 0)} pages previously crawled")
                    return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
        
        return None
