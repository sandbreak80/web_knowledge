"""Setup script for WebArc package."""

from setuptools import setup, find_packages

setup(
    name="webarc",
    version="1.0.0",
    description="Local web documentation to Obsidian Markdown extractor",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "scrapy==2.11.0",
        "scrapy-playwright==0.0.34",
        "playwright==1.40.0",
        "readability-lxml==0.8.1",
        "trafilatura==1.6.2",
        "markdownify==0.11.6",
        "publicsuffix2==2.20191221",
        "idna==3.6",
        "orjson==3.9.10",
        "typer==0.9.0",
        "rich==13.7.0",
        "pydantic==2.5.0",
        "beautifulsoup4==4.12.0",
        "lxml==4.9.3",
        "pyyaml==6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "webarc=webarc.cli.commands:main",
        ],
    },
)
