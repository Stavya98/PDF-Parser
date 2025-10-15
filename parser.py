import fitz  # import PyMuPDF
import re
import os
import sys
import argparse
from textwrap import dedent

# python parser.py "C:\Users\Stavya\Downloads\hdfc_sample_statement.pdf"

class BaseParser:
    """Base class for all statement parsers."""
    issuer_name = "Unknown"
    required_keywords = []

    @classmethod
    def identify(cls, text):
        """Check if the text contains all required keywords for this issuer."""
        return all(keyword in text for keyword in cls.required_keywords)

    @staticmethod
    def extract(text):
        """Extracts data points from the text. To be implemented by subclasses."""
        raise NotImplementedError

class HDFCParser(BaseParser):
    """Parses HDFC Bank credit card statements."""
    issuer_name = "HDFC Bank"
    required_keywords = ["HDFC BANK"]

    @staticmethod
    def extract(text):
        data = {}
        name_match = re.search(r"Name:\s+([A-Z\s]+)\n", text)
        if name_match:
            data['Cardholder Name'] = name_match.group(1).strip()

        card_match = re.search(r"Card No:\s+XXXX XXXX XXXX (\d{4})", text)
        if card_match:
            data['Card Last 4 Digits'] = card_match.group(1)

        due_date_match = re.search(r"Payment Due Date:\s*(\d{2}-\d{2}-\d{4})", text)
        if due_date_match:
            data['Payment Due Date'] = due_date_match.group(1)

        balance_match = re.search(r"Total Dues\s+([\d,]+\.\d{2})", text)
        if balance_match:
            data['Total Balance Due'] = f"₹{balance_match.group(1)}"

        period_match = re.search(r"Statement Date\s*(\d{2}-\d{2}-\d{4})", text)
        if period_match:
            data['Billing Cycle'] = f"Statement Date: {period_match.group(1)}"
        return data

class ChaseParser(BaseParser):
    """Parses Chase credit card statements."""
    issuer_name = "Chase"
    required_keywords = ["chase.com"]

    @staticmethod
    def extract(text):
        return {}

class AmexParser(BaseParser):
    """Parses American Express credit card statements."""
    issuer_name = "American Express"
    required_keywords = ["american express"]

    @staticmethod
    def extract(text):
        data = {}
        name_match = re.search(r"Prepared for:\s+([A-Z\s]+),", text)
        if name_match:
            data['Cardholder Name'] = name_match.group(1).strip()

        balance_match = re.finditer(r'New Balance\s+\$([\d,]+\.\d{2})', text)
        if balance_match:
            data['Total Balance Due'] = f"${balance_match.group(1)}"
            
        return data

class CapitalOneParser(BaseParser):
    """Parses Capital One credit card statements."""
    issuer_name = "Capital One"
    required_keywords = ["capital one"]
    @staticmethod
    def extract(text): return {}

class BankOfAmericaParser(BaseParser):
    """Parses Bank of America credit card statements."""
    issuer_name = "Bank of America"
    required_keywords = ["bank of america"]
    @staticmethod
    def extract(text): return {}

class CitiParser(BaseParser):
    """Parses Citi credit card statements."""
    issuer_name = "Citi"
    required_keywords = ["citi.com"]
    @staticmethod
    def extract(text): return {}


# List of all available parser classes
ALL_PARSERS = [HDFCParser, ChaseParser, AmexParser, CapitalOneParser, BankOfAmericaParser, CitiParser]
ALL_KEYS = ['Cardholder Name', 'Card Last 4 Digits', 'Payment Due Date', 'Total Balance Due', 'Billing Cycle']

def get_parser(text):
    """Identifies and returns the correct parser for the given text."""
    for parser in ALL_PARSERS:
        if parser.identify(text):
            return parser
    return None

def process_pdf(filepath):
    """
    Opens a PDF, extracts text, identifies the issuer, parses the data,
    and prints the results to the console.
    """
    print(f"[*] Processing file: {os.path.basename(filepath)}")
    try:
        text = ""
        with fitz.open(filepath) as doc:
            if not doc:
                print("[!] Error: Could not open the PDF document.", file=sys.stderr)
                return
            if len(doc) > 0:
                page = doc.load_page(0)
                text = ' '.join(page.get_text().split())
        
        if not text.strip():
            print("[!] Error: No text found on the first page.", file=sys.stderr)
            return

        parser = get_parser(text)
        
        if not parser:
            print("[!] Error: Could not identify the credit card issuer.", file=sys.stderr)
            return
        
        print(f"[+] Issuer Detected: {parser.issuer_name}")
        
        extracted_data = parser.extract(text)
        
        if not extracted_data:
             print("\n" + "="*25)
             print("  No data could be extracted.")
             print("="*25 + "\n")
             return

        print("\n" + "="*25)
        print("   Extraction Results")
        print("="*25)
        for key in ALL_KEYS:
            value = extracted_data.get(key, 'Not Found')
            print(f"  {key:<20}: {value}")
        print("="*25 + "\n")

    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}", file=sys.stderr)

def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description="A command-line tool to parse PDF credit card statements.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=dedent("""
        Example Usage:
        --------------
        python parser_cli.py "/path/to/your/statement.pdf"
        """)
    )
    parser.add_argument("filepath", help="The full path to the PDF statement file.")
    
    args = parser.parse_args()
    
    process_pdf(args.filepath)

if __name__ == '__main__':
    main()