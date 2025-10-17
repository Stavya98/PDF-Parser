import fitz  # PyMuPDF
import re
import os
import sys
import argparse
from textwrap import dedent
# python parser.py "statement.pdf"
# python demo.py "C:\Users\Stavya\Downloads\hdfc_sample_statement.pdf"

PARSER_CONFIGS = [
    {
        "issuer_name": "HDFC Bank",
        "required_keywords": ["hdfc bank", "hdfc", "hdfccreditcard"],
        "patterns": {
            'Cardholder Name': r"Name\s*:\s*([A-Za-z\s]+)",
            'Card Last 4 Digits': r"Card No\.\s*:.*?(\d{4})",
            'Payment Due Date': r"Payment Due Date\s*:\s*(\d{2}/\d{2}/\d{4})",
            'Total Balance Due': (r"Total Dues\s*:\s*([\d,]+\.\d{2})", lambda m: f"₹{m.group(1)}"),
            'Billing Cycle': (r"Statement Date\s*:\s*(\d{2}/\d{2}/\d{4})", lambda m: f"Statement Date: {m.group(1)}")
        }
    },
    {
        "issuer_name": "ICICI Bank",
        "required_keywords": ["icici bank"],
        "patterns": {
            'Cardholder Name': r"Name\s*:\s*([A-Z\s]+)",
            'Card Last 4 Digits': r"Card Number\s*:.*?(\d{4})",
            'Payment Due Date': r"Payment Due Date\s*:\s*(\d{2}-\d{2}-\d{4})",
            'Total Balance Due': (r"Total Amount Due\s*₹\s*([\d,]+\.\d{2})", lambda m: f"₹{m.group(1)}"),
            'Billing Cycle': (r"Statement Date\s*:\s*(\d{2}-\d{2}-\d{4})", lambda m: f"Statement Date: {m.group(1)}")
        }
    },
    {
        "issuer_name": "SBI Card",
        "required_keywords": ["sbi card", "sbicard.com"],
        "patterns": {
            'Cardholder Name': r"SUMMARY OF ACCOUNT\s*\n\s*([A-Z\s]+)",
            'Card Last 4 Digits': r"SBI Card No\..*?(\d{4})",
            'Payment Due Date': r"Payment Due Date\s*:\s*(\d{2}-\w{3}-\d{2})",
            'Total Balance Due': (r"Total Amount Due\s*Rs\. ([\d,]+\.\d{2})", lambda m: f"₹{m.group(1)}"),
            'Billing Cycle': (r"Statement Date\s*:\s*(\d{2}-\w{3}-\d{2})", lambda m: f"Statement Date: {m.group(1)}")
        }
    },
    {
        "issuer_name": "Axis Bank",
        "required_keywords": ["axis bank"],
        "patterns": {
            'Cardholder Name': r"MR/MS\s+([A-Z\s]+)",
            'Card Last 4 Digits': r"Card Number\s*:.*?(\d{4})",
            'Payment Due Date': r"Payment Due Date\s+(\d{2}-\w{3}-\d{2})",
            'Total Balance Due': (r"TOTAL AMOUNT DUE\s+INR\s+([\d,]+\.\d{2})", lambda m: f"₹{m.group(1)}"),
            'Billing Cycle': (r"Statement Period\s*:\s*(\d{2}/\d{2}/\d{4} to \d{2}/\d{2}/\d{4})", lambda m: m.group(1))
        }
    },
    {
        "issuer_name": "American Express",
        "required_keywords": ["american express"],
        "patterns": {
            'Cardholder Name': r"Prepared for\s+([A-Z\s]+)",
            'Card Last 4 Digits': (r'Account Number\s+\d{5} \d{5} (\d{5})', lambda m: m.group(1)[-4:]),
            'Payment Due Date': r'Please pay by\s+(\w+\s\d{1,2})',
            'Total Balance Due': (r'New Balance\s+₹([\d,]+\.\d{2})', lambda m: f"₹{m.group(1)}"),
            'Billing Cycle': (r'Closing date\s+(\w+\s\d{1,2},\s\d{4})', lambda m: f"Ending on {m.group(1)}")
        }
    }
]

ALL_KEYS = ['Cardholder Name', 'Card Last 4 Digits', 'Payment Due Date', 'Total Balance Due', 'Billing Cycle']

def process_pdf(filepath):
    #Opens and processes a single PDF file
    print(f" Processing file: {os.path.basename(filepath)}")
    try:
        with fitz.open(filepath) as doc:
            text = ""
            # Combine text from all pages to ensure data is found
            for page in doc:
                text += page.get_text()

        if not text.strip():
            print(" Error: No text found in the PDF.", file=sys.stderr)
            return

        # Identify and extract data
        matched_parser = None
        for config in PARSER_CONFIGS:
            if any(keyword.lower() in text.lower() for keyword in config["required_keywords"]):
                matched_parser = config
                break

        if not matched_parser:
            print(" Error: Could not identify the credit card issuer.", file=sys.stderr)
            return

        print(f"Issuer Detected: {matched_parser['issuer_name']}")
        extracted_data = {}
        for key, pattern_config in matched_parser["patterns"].items():
            regex, formatter = (pattern_config[0], pattern_config[1]) if isinstance(pattern_config, tuple) else (pattern_config, None)
            
            flags = re.DOTALL | re.IGNORECASE
            match = re.search(regex, text, flags)
            
            if match:
                if formatter:
                    extracted_data[key] = formatter(match)
                else:
                    # Use group(1) if a capturing group is present, otherwise group(0)
                    extracted_data[key] = match.group(1).strip() if match.groups() else match.group(0).strip()
        
        # Print results
        print("\n" + "="*25)
        print("   Extraction Results ")
        print("="*25)
        for key in ALL_KEYS:
            value = extracted_data.get(key, 'Not Found')
            print(f"  {key:<20}: {value}")
        print("="*25 + "\n")

    except Exception as e:
        print(f" An unexpected error occurred: {e}", file=sys.stderr)
        print("    The PDF might be corrupted or password-protected.", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="A command-line tool to parse PDF credit card statements.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=dedent(""" run it as python parser.py "/path/to/statement.pdf"
        """)
    )
    parser.add_argument("filepath", help="The full path to the PDF statement file.")
    args = parser.parse_args()
    process_pdf(args.filepath)

if __name__ == '__main__':
    main()