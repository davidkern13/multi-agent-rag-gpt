"""
PDF Downloader

Downloads SEC filing PDF for corpus
"""

import os
import requests
from pathlib import Path


def download_pdf(
    url: str = "https://ir.bigbear.ai/sec-filings/all-sec-filings/content/0001836981-25-000028/0001836981-25-000028.pdf",
    output_path: str = "data/corpus.pdf"
) -> str:
    """
    Download PDF from URL.
    
    Args:
        url: PDF URL
        output_path: Where to save
        
    Returns:
        Path to downloaded file
    """
    # Create directory if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already exists
    if os.path.exists(output_path):
        print(f"✅ PDF already exists: {output_path}")
        return output_path
    
    print(f"📥 Downloading PDF from: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        size_mb = len(response.content) / (1024 * 1024)
        print(f"✅ Downloaded: {output_path} ({size_mb:.2f} MB)")
        
        return output_path
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        raise


def get_corpus_path(auto_download: bool = True) -> str:
    """
    Get path to corpus PDF, download if needed.
    
    Args:
        auto_download: Download if not exists
        
    Returns:
        Path to corpus.pdf
    """
    corpus_path = "data/corpus.pdf"
    
    if os.path.exists(corpus_path):
        return corpus_path
    
    if auto_download:
        return download_pdf()
    
    raise FileNotFoundError(f"Corpus not found: {corpus_path}")


if __name__ == "__main__":
    download_pdf()