"""Output file writer with deduplication."""

import hashlib
import re
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class OutputWriter:
    """
    Write extracted content to filesystem with deduplication.
    """
    
    def __init__(self, output_dir: Path, config):
        """
        Initialize output writer.
        
        Args:
            output_dir: Output directory path
            config: WebArc configuration
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self.url_to_file: Dict[str, Path] = {}
        self.content_hashes: Dict[str, Path] = {}
        
        # Create output directory structure
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir = self.output_dir / '_attachments'
        self.attachments_dir.mkdir(exist_ok=True)
    
    def write_page(self, url: str, content: Dict[str, Any]) -> Path:
        """
        Write page to filesystem with deduplication.
        
        Args:
            url: Source URL
            content: Dict with keys: markdown, metadata, content_hash
        
        Returns:
            Path to written file
        """
        # Calculate content hash if not provided
        content_hash = content.get('content_hash')
        if not content_hash:
            content_hash = self._calculate_hash(content.get('markdown', ''))
        
        # Check for duplicate content
        if content_hash in self.content_hashes:
            existing_file = self.content_hashes[content_hash]
            new_file = self.url_to_filepath(url)
            
            # Create symlink
            new_file.parent.mkdir(parents=True, exist_ok=True)
            if not new_file.exists():
                try:
                    new_file.symlink_to(existing_file.relative_to(new_file.parent))
                except Exception:
                    # Symlink failed, write duplicate
                    pass
            
            logger.info(f"Duplicate content, symlinked: {new_file} → {existing_file}")
            return new_file
        
        # Generate file path
        file_path = self.url_to_filepath(url)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle filename collisions
        file_path = self._handle_collision(file_path)
        
        # Write file with front-matter
        full_content = self._format_with_frontmatter(content)
        
        # Write to disk
        file_path.write_text(full_content, encoding='utf-8')
        
        # Track mappings
        self.url_to_file[url] = file_path
        self.content_hashes[content_hash] = file_path
        
        logger.info(f"Wrote: {file_path}")
        return file_path
    
    def url_to_filepath(self, url: str) -> Path:
        """
        Convert URL to filesystem path.
        
        Example:
        https://docs.appdynamics.com/appd/24.x/en/page-title
        → output/docs.appdynamics.com/appd/24.x/en/page-title.md
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # Start with domain
        parts = [parsed.netloc.lower()]
        
        # Add path segments
        path_segments = [p for p in parsed.path.split('/') if p]
        
        # Sanitize each segment
        sanitized = [self._sanitize_filename(seg) for seg in path_segments]
        parts.extend(sanitized)
        
        # Build path
        rel_path = Path(*parts)
        
        # Add .md extension if not present
        if not rel_path.suffix:
            rel_path = rel_path.with_suffix('.md')
        elif rel_path.suffix not in ['.md', '.markdown']:
            # Has other extension, append .md
            rel_path = Path(str(rel_path) + '.md')
        
        # Handle index files (make visible)
        if rel_path.name == 'index.md':
            rel_path = rel_path.parent / '_index.md'
        
        return self.output_dir / rel_path
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Remove/replace invalid filename characters.
        
        Invalid: < > : " | ? * \ / (on Windows)
        """
        # Remove invalid chars
        invalid_chars = r'[<>:"|?*\\/]'
        sanitized = re.sub(invalid_chars, '-', name)
        
        # Collapse multiple dashes
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Trim dashes from edges
        sanitized = sanitized.strip('-')
        
        # Truncate if too long
        max_len = self.config.output.max_filename_length
        if len(sanitized) > max_len:
            # Keep extension
            if '.' in sanitized:
                name_part, ext = sanitized.rsplit('.', 1)
                sanitized = name_part[:max_len - len(ext) - 1] + '.' + ext
            else:
                sanitized = sanitized[:max_len]
        
        # Ensure not empty
        if not sanitized:
            sanitized = 'unnamed'
        
        return sanitized
    
    def _handle_collision(self, path: Path) -> Path:
        """Handle filename collisions by appending -2, -3, etc."""
        if not path.exists():
            return path
        
        # File exists, find available name
        counter = 2
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        while True:
            new_name = f"{stem}-{counter}{suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            if counter > 1000:
                raise RuntimeError(f"Too many collisions for: {path}")
    
    def _format_with_frontmatter(self, content: Dict[str, Any]) -> str:
        """Format Markdown with YAML front-matter."""
        import yaml
        
        metadata = content.get('metadata', {})
        markdown = content.get('markdown', '')
        
        # Build YAML front-matter
        yaml_lines = ['---']
        
        # Add standard fields
        for key, value in metadata.items():
            if value is None:
                continue
            
            if isinstance(value, (list, dict)):
                # Use YAML formatting for complex types
                yaml_lines.append(f"{key}:")
                yaml_value = yaml.dump(value, default_flow_style=False, allow_unicode=True)
                for line in yaml_value.split('\n'):
                    if line:
                        yaml_lines.append(f"  {line}")
            else:
                # Simple key: value
                value_str = str(value).replace('"', '\\"')
                if ':' in value_str or '\n' in value_str:
                    yaml_lines.append(f'{key}: "{value_str}"')
                else:
                    yaml_lines.append(f'{key}: {value_str}')
        
        yaml_lines.append('---')
        yaml_lines.append('')  # Blank line after front-matter
        
        # Combine front-matter and content
        full_content = '\n'.join(yaml_lines) + markdown
        
        return full_content
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
