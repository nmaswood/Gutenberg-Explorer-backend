from bs4 import BeautifulSoup
import re
from typing import Dict, Any
import logging
from urllib.parse import urljoin


def parse_gutenberg_rdf_metadata(xml_content: str) -> Dict[str, Any]:
    """
    Parse Project Gutenberg RDF/XML metadata and return a dictionary.

    Args:
        xml_content (str): RDF/XML content from a Project Gutenberg metadata file
        
    Returns:
        Dict[str, Any]: Dictionary containing parsed book metadata
    """
    try:
        # Parse the XML with BeautifulSoup
        soup = BeautifulSoup(xml_content, 'lxml-xml')
        
        # Initialize metadata dictionary
        metadata = {}

        # Extract title
        title = soup.find('dcterms:title')
        if title:
            metadata['title'] = title.text.strip()

        # Extract publisher
        publisher = soup.find('dcterms:publisher')
        if publisher:
            metadata['publisher'] = publisher.text.strip()

        # Extract rights
        rights = soup.find('dcterms:rights')
        if rights:
            metadata['rights'] = rights.text.strip()

        # Extract language
        language = soup.find('dcterms:language')
        if language:
            lang_value = language.find('rdf:value')
            if lang_value:
                metadata['language'] = lang_value.text.strip()

        # Extract publication date
        issued = soup.find('dcterms:issued')
        if issued:
            metadata['issued'] = issued.text.strip()

        # Extract author information
        creator = soup.find('dcterms:creator')
        if creator:
            author = creator.find('pgterms:agent')
            if author:
                author_name = author.find('pgterms:name')
                if author_name:
                    metadata['author_name'] = author_name.text.strip()
                
                birth_date = author.find('pgterms:birthdate')
                if birth_date:
                    metadata['author_birthdate'] = birth_date.text.strip()
                
                death_date = author.find('pgterms:deathdate')
                if death_date:
                    metadata['author_deathdate'] = death_date.text.strip()
                
                webpage = author.find('pgterms:webpage')
                if webpage:
                    metadata['author_webpage'] = webpage['rdf:resource']

        # Extract download information
        downloads = soup.find('pgterms:downloads')
        if downloads:
            metadata['downloads'] = downloads.text.strip()

        # Extract formats
        formats = []
        for file in soup.find_all('pgterms:file'):
            format_info = {
                'url': file['rdf:about'],
                'size': file.find('dcterms:extent').text if file.find('dcterms:extent') else None,
                'format': file.find('rdf:value').text if file.find('rdf:value') else None,
                'modified': file.find('dcterms:modified').text if file.find('dcterms:modified') else None,
            }
            formats.append(format_info)
        if formats:
            metadata['formats'] = formats

        return metadata

    except Exception as e:
        print(f"Error parsing metadata: {e}")
        return {}