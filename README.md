PubMed Papers Fetcher
A command-line tool to fetch research papers from PubMed and identify those with pharmaceutical/biotech company affiliations.

Features
Search PubMed using full query syntax
Identify papers with authors affiliated with pharmaceutical/biotech companies
Extract key information: PMID, title, publication date, non-academic authors, company affiliations, and corresponding author email
Export results to CSV format
Command-line interface with debug mode
Installation
Prerequisites
Python 3.8 or higher
Poetry (for dependency management)
Setup
Clone the repository:
bash
git clone <repository-url>
cd pubmed-papers-fetcher
Install dependencies using Poetry:
bash
poetry install
Activate the virtual environment:
bash
poetry shell
Usage
Basic Usage
bash
get-papers-list "your search query"
Command-line Options
query: Search query for PubMed (required)
-f, --file: Output CSV filename (default: pubmed_results.csv)
-d, --debug: Enable debug output
-h, --help: Show help message
Examples
bash
# Basic search
get-papers-list "cancer treatment"

# Specify output file
get-papers-list "COVID-19 vaccine" --file covid_results.csv

# Enable debug mode
get-papers-list "drug development" --debug

# Complex query with PubMed syntax
get-papers-list "breast cancer[Title] AND drug therapy[MeSH Terms]"
Output Format
The tool generates a CSV file with the following columns:

PubmedID: Unique identifier for the paper
Title: Title of the paper
Publication Date: Date the paper was published
Non-academic Author(s): Names of authors affiliated with non-academic institutions
Company Affiliation(s): Names of pharmaceutical/biotech companies
Corresponding Author Email: Email address of the corresponding author
Code Organization
The project is organized as follows:

pubmed-papers-fetcher/
├── get_papers_list/
│   ├── __init__.py
│   └── main.py          # Main application logic
├── tests/               # Test files
├── pyproject.toml       # Poetry configuration
├── README.md           # This file
└── .gitignore          # Git ignore file
How It Works
Search: Uses PubMed's E-utilities API to search for papers matching the query
Fetch Details: Retrieves detailed information for each paper including authors and affiliations
Filter: Identifies papers with pharmaceutical/biotech company affiliations by:
Checking author affiliations against a comprehensive list of known companies
Identifying industry keywords in affiliations
Filtering out academic institutions studying these companies
Export: Saves results to a CSV file with all required columns
Company Detection
The tool identifies pharmaceutical and biotech companies using:

A comprehensive list of major pharmaceutical companies (Pfizer, Moderna, Johnson & Johnson, etc.)
Biotech companies (Biogen, Regeneron, Vertex, etc.)
Life sciences companies (Thermo Fisher, Illumina, etc.)
Industry keywords (pharmaceutical, biotech, therapeutics, etc.)
Common corporate suffixes (Inc., Corp., Ltd., etc.)
API Rate Limiting
The tool implements respectful API usage:

Processes papers in batches of 200
Includes delays between batch requests
Handles API errors gracefully
Development
Running Tests
bash
poetry run pytest
Code Formatting
bash
poetry run black .
poetry run flake8 .
Adding Dependencies
bash
poetry add <package-name>
Dependencies
requests: For making HTTP requests to PubMed API
xml.etree.ElementTree: For parsing XML responses (built-in)
csv: For CSV file generation (built-in)
argparse: For command-line interface (built-in)
Contributing
Fork the repository
Create a feature branch
Make your changes
Add tests for new functionality
Submit a pull request
License
This project is licensed under the MIT License.

Troubleshooting
Common Issues
No papers found: Check your query syntax and try broader terms
API errors: The PubMed API may be temporarily unavailable; try again later
Empty results: Your query might be too specific or the papers might not have industry affiliations
Debug Mode
Use the --debug flag to see detailed information about the search and processing:

bash
get-papers-list "your query" --debug
This will show:

Search parameters
Number of papers found
Processing progress
Any errors encountered
Future Enhancements
Support for additional databases (PMC, Crossref)
More sophisticated company detection algorithms
Export to additional formats (JSON, Excel)
Web interface
Configuration file support
Advanced filtering options
# Pubmed_Paper_Fetcher
