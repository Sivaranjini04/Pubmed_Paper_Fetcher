#!/usr/bin/env python3
"""
PubMed Papers Fetcher
A command-line tool to fetch research papers from PubMed and identify those with 
pharmaceutical/biotech company affiliations.
"""

import argparse
import csv
import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time
import re
from typing import List, Dict, Optional, Set

class PubMedFetcher:
    """Handles fetching and parsing PubMed data."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Common pharmaceutical and biotech companies
    PHARMA_BIOTECH_COMPANIES = {
        'pfizer', 'moderna', 'johnson & johnson', 'merck', 'abbott', 'roche',
        'novartis', 'gsk', 'glaxosmithkline', 'sanofi', 'bristol myers squibb',
        'astrazeneca', 'eli lilly', 'gilead', 'amgen', 'biogen', 'regeneron',
        'vertex', 'genentech', 'takeda', 'bayer', 'boehringer ingelheim',
        'celgene', 'abbvie', 'illumina', 'thermo fisher', 'danaher',
        'agilent', 'waters', 'applied biosystems', 'life technologies',
        'bio-rad', 'qiagen', 'promega', 'new england biolabs', 'neb',
        'invitrogen', 'sigma-aldrich', 'merck kgaa', 'eppendorf',
        'beckman coulter', 'bd', 'becton dickinson', 'medtronic',
        'stryker', 'boston scientific', 'edwards lifesciences',
        'intuitive surgical', 'zimmer biomet', 'smith & nephew',
        'pharmaceutical', 'pharmaceuticals', 'biotech', 'biotechnology',
        'biopharmaceutical', 'biopharmaceuticals', 'drug development',
        'therapeutics', 'pharma', 'inc.', 'corp.', 'corporation',
        'company', 'ltd.', 'limited', 'sa', 'ag', 'gmbh'
    }
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.session = requests.Session()
        
    def log(self, message: str):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr)
    
    def search_papers(self, query: str, max_results: int = 100) -> List[str]:
        """Search PubMed for papers and return list of PMIDs."""
        self.log(f"Searching PubMed for: {query}")
        
        search_url = f"{self.BASE_URL}esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml'
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            pmids = [id_elem.text for id_elem in root.findall('.//Id')]
            
            self.log(f"Found {len(pmids)} papers")
            return pmids
            
        except requests.RequestException as e:
            print(f"Error searching PubMed: {e}", file=sys.stderr)
            return []
        except ET.ParseError as e:
            print(f"Error parsing search results: {e}", file=sys.stderr)
            return []
    
    def fetch_paper_details(self, pmids: List[str]) -> List[Dict]:
        """Fetch detailed information for given PMIDs."""
        if not pmids:
            return []
            
        self.log(f"Fetching details for {len(pmids)} papers")
        
        # Process in batches to avoid overwhelming the API
        batch_size = 200
        all_papers = []
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            batch_papers = self._fetch_batch_details(batch)
            all_papers.extend(batch_papers)
            
            # Be respectful to the API
            if i + batch_size < len(pmids):
                time.sleep(0.5)
        
        return all_papers
    
    def _fetch_batch_details(self, pmids: List[str]) -> List[Dict]:
        """Fetch details for a batch of PMIDs."""
        fetch_url = f"{self.BASE_URL}efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml'
        }
        
        try:
            response = self.session.get(fetch_url, params=params)
            response.raise_for_status()
            
            return self._parse_paper_details(response.content)
            
        except requests.RequestException as e:
            print(f"Error fetching paper details: {e}", file=sys.stderr)
            return []
        except ET.ParseError as e:
            print(f"Error parsing paper details: {e}", file=sys.stderr)
            return []
    
    def _parse_paper_details(self, xml_content: bytes) -> List[Dict]:
        """Parse XML content and extract paper details."""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                paper = self._extract_paper_info(article)
                if paper:
                    papers.append(paper)
                    
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}", file=sys.stderr)
            
        return papers
    
    def _extract_paper_info(self, article_elem) -> Optional[Dict]:
        """Extract information from a single PubmedArticle element."""
        try:
            # Extract PMID
            pmid_elem = article_elem.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else ""
            
            # Extract title
            title_elem = article_elem.find('.//ArticleTitle')
            title = self._get_text_content(title_elem) if title_elem is not None else ""
            
            # Extract publication date
            pub_date = self._extract_publication_date(article_elem)
            
            # Extract author information
            authors_info = self._extract_authors_info(article_elem)
            
            # Check for pharmaceutical/biotech affiliations
            company_affiliations = self._identify_company_affiliations(authors_info['all_affiliations'])
            non_academic_authors = self._identify_non_academic_authors(authors_info['authors'])
            
            # Extract corresponding author email
            corresponding_email = self._extract_corresponding_email(article_elem)
            
            paper_info = {
                'PubmedID': pmid,
                'Title': title,
                'Publication Date': pub_date,
                'Non-academic Author(s)': '; '.join(non_academic_authors),
                'Company Affiliation(s)': '; '.join(company_affiliations),
                'Corresponding Author Email': corresponding_email
            }
            
            return paper_info
            
        except Exception as e:
            self.log(f"Error extracting paper info: {e}")
            return None
    
    def _get_text_content(self, elem) -> str:
        """Get text content from XML element, handling nested elements."""
        if elem is None:
            return ""
        
        # Get all text content, including from nested elements
        text_parts = []
        if elem.text:
            text_parts.append(elem.text)
        
        for child in elem:
            text_parts.append(self._get_text_content(child))
            if child.tail:
                text_parts.append(child.tail)
        
        return ''.join(text_parts).strip()
    
    def _extract_publication_date(self, article_elem) -> str:
        """Extract publication date from article element."""
        # Try different date fields
        date_fields = [
            './/PubDate',
            './/ArticleDate',
            './/DateCompleted',
            './/DateRevised'
        ]
        
        for field in date_fields:
            date_elem = article_elem.find(field)
            if date_elem is not None:
                year = date_elem.find('Year')
                month = date_elem.find('Month')
                day = date_elem.find('Day')
                
                date_parts = []
                if year is not None and year.text:
                    date_parts.append(year.text)
                if month is not None and month.text:
                    date_parts.append(month.text)
                if day is not None and day.text:
                    date_parts.append(day.text)
                
                if date_parts:
                    return '-'.join(date_parts)
        
        return ""
    
    def _extract_authors_info(self, article_elem) -> Dict:
        """Extract author names and affiliations."""
        authors = []
        all_affiliations = []
        
        author_list = article_elem.find('.//AuthorList')
        if author_list is not None:
            for author in author_list.findall('Author'):
                # Extract author name
                lastname = author.find('LastName')
                forename = author.find('ForeName')
                
                if lastname is not None and lastname.text:
                    author_name = lastname.text
                    if forename is not None and forename.text:
                        author_name = f"{forename.text} {lastname.text}"
                    
                    # Extract affiliations for this author
                    author_affiliations = []
                    for affiliation in author.findall('.//Affiliation'):
                        if affiliation.text:
                            affiliation_text = affiliation.text.strip()
                            author_affiliations.append(affiliation_text)
                            all_affiliations.append(affiliation_text)
                    
                    authors.append({
                        'name': author_name,
                        'affiliations': author_affiliations
                    })
        
        return {
            'authors': authors,
            'all_affiliations': all_affiliations
        }
    
    def _identify_company_affiliations(self, affiliations: List[str]) -> List[str]:
        """Identify pharmaceutical/biotech company affiliations."""
        company_affiliations = set()
        
        for affiliation in affiliations:
            affiliation_lower = affiliation.lower()
            
            # Check for known company names
            for company in self.PHARMA_BIOTECH_COMPANIES:
                if company in affiliation_lower:
                    # Extract the relevant part of the affiliation
                    company_affiliations.add(affiliation.strip())
                    break
        
        return list(company_affiliations)
    
    def _identify_non_academic_authors(self, authors: List[Dict]) -> List[str]:
        """Identify authors with non-academic affiliations."""
        non_academic_authors = []
        
        for author in authors:
            is_non_academic = False
            
            for affiliation in author['affiliations']:
                affiliation_lower = affiliation.lower()
                
                # Check if affiliation contains industry keywords
                if any(keyword in affiliation_lower for keyword in self.PHARMA_BIOTECH_COMPANIES):
                    # Also check it's not a university department studying these companies
                    if not any(academic_keyword in affiliation_lower for academic_keyword in 
                             ['university', 'college', 'school', 'institute', 'department', 'center', 'centre']):
                        is_non_academic = True
                        break
            
            if is_non_academic:
                non_academic_authors.append(author['name'])
        
        return non_academic_authors
    
    def _extract_corresponding_email(self, article_elem) -> str:
        """Extract corresponding author email if available."""
        # Look for email addresses in various locations
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Check affiliations for email addresses
        for affiliation in article_elem.findall('.//Affiliation'):
            if affiliation.text:
                emails = re.findall(email_pattern, affiliation.text)
                if emails:
                    return emails[0]
        
        # Check author information
        for author in article_elem.findall('.//Author'):
            author_text = ET.tostring(author, encoding='unicode')
            emails = re.findall(email_pattern, author_text)
            if emails:
                return emails[0]
        
        return ""

def write_csv(papers: List[Dict], filename: str):
    """Write papers data to CSV file."""
    if not papers:
        print("No papers to write to CSV.", file=sys.stderr)
        return
    
    fieldnames = ['PubmedID', 'Title', 'Publication Date', 'Non-academic Author(s)', 
                  'Company Affiliation(s)', 'Corresponding Author Email']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(papers)
        
        print(f"Results written to {filename}")
        
    except IOError as e:
        print(f"Error writing CSV file: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description='Fetch research papers from PubMed and identify those with pharmaceutical/biotech company affiliations.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "cancer treatment"
  %(prog)s "COVID-19 vaccine" --file results.csv
  %(prog)s "drug development" --debug
        """
    )
    
    parser.add_argument('query', help='Search query for PubMed')
    parser.add_argument('-f', '--file', default='pubmed_results.csv',
                       help='Output CSV filename (default: pubmed_results.csv)')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='Enable debug output')
    
    args = parser.parse_args()
    
    if args.debug:
        print(f"[DEBUG] Query: {args.query}", file=sys.stderr)
        print(f"[DEBUG] Output file: {args.file}", file=sys.stderr)
    
    # Initialize fetcher
    fetcher = PubMedFetcher(debug=args.debug)
    
    # Search for papers
    pmids = fetcher.search_papers(args.query)
    
    if not pmids:
        print("No papers found for the given query.", file=sys.stderr)
        return 1
    
    # Fetch paper details
    papers = fetcher.fetch_paper_details(pmids)
    
    if not papers:
        print("No paper details could be retrieved.", file=sys.stderr)
        return 1
    
    # Filter papers with pharmaceutical/biotech affiliations
    filtered_papers = [paper for paper in papers 
                      if paper['Company Affiliation(s)'] or paper['Non-academic Author(s)']]
    
    print(f"Found {len(papers)} total papers")
    print(f"Found {len(filtered_papers)} papers with pharmaceutical/biotech affiliations")
    
    # Write results to CSV
    write_csv(filtered_papers, args.file)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
