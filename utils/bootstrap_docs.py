"""Utility for managing Bootstrap documentation files with Gemini"""

import os
import glob
from openai import OpenAI # Import OpenAI
from typing import Optional, List, Dict, Tuple
from utils.api_keys import get_openai_key # Use get_openai_key

def get_bootstrap_docs_dir():
    """Get the path to Bootstrap docs directory"""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(current_dir, 'docs', 'bootstrap')
    return docs_dir

def find_bootstrap_docs() -> List[str]:
    """Find all Bootstrap documentation files"""
    docs_dir = get_bootstrap_docs_dir()
    if not os.path.exists(docs_dir):
        return []
    
    # Look for common documentation file extensions - skip README.md
    patterns = ['*.pdf']  # Only PDF files for Bootstrap docs
    files = []
    for pattern in patterns:
        found_files = glob.glob(os.path.join(docs_dir, pattern))
        # Filter out README.md
        files.extend([f for f in found_files if not os.path.basename(f).lower().startswith('readme')])
        found_files_recursive = glob.glob(os.path.join(docs_dir, '**', pattern), recursive=True)
        files.extend([f for f in found_files_recursive if not os.path.basename(f).lower().startswith('readme')])
    
    return files

def get_or_upload_bootstrap_docs(openai_client: OpenAI) -> List[Tuple[str, str]]: # Change client type
    """Get existing uploaded Bootstrap docs or upload new ones"""
    return [] # Currently disabled, returns empty list

