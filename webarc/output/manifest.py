"""Manifest and graph writers for crawl metadata."""

import logging
from pathlib import Path
from typing import Dict, Any
import orjson

logger = logging.getLogger(__name__)


class ManifestWriter:
    """
    Write manifest.jsonl, graph.jsonl, and errors.jsonl files.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize manifest writer.
        
        Args:
            output_dir: Output directory
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.manifest_file = self.output_dir / 'manifest.jsonl'
        self.graph_file = self.output_dir / 'graph.jsonl'
        self.errors_file = self.output_dir / 'errors.jsonl'
    
    def write_manifest_entry(self, entry: Dict[str, Any]):
        """
        Write entry to manifest.jsonl.
        
        Args:
            entry: Manifest entry dictionary
        """
        with open(self.manifest_file, 'ab') as f:
            f.write(orjson.dumps(entry) + b'\n')
    
    def write_graph_entry(self, entry: Dict[str, Any]):
        """
        Write entry to graph.jsonl.
        
        Args:
            entry: Graph entry dictionary
        """
        with open(self.graph_file, 'ab') as f:
            f.write(orjson.dumps(entry) + b'\n')
    
    def write_error_entry(self, entry: Dict[str, Any]):
        """
        Write entry to errors.jsonl.
        
        Args:
            entry: Error entry dictionary
        """
        with open(self.errors_file, 'ab') as f:
            f.write(orjson.dumps(entry) + b'\n')
