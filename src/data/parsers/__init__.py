"""Parser registry for log ingestion."""

from .basic_text import parse_line as basic_text_parser

__all__ = ["basic_text_parser"]
