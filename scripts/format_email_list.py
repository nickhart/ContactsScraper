#!/usr/bin/env python3
import csv
import argparse

def main():
    parser = argparse.ArgumentParser(description="Format contacts CSV into an email list.")
    parser.add_argument("--input", required=True, help="Path to the input CSV file with contacts")
    parser.add_argument("--output", required=True, help="Path to the output file for the email list")
    parser.add_argument("--separator", type=str, default="\n",
                        help="Separator to use between email addresses (default: newline)")
    args = parser.parse_args()

    contacts = []
    with open(args.input, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row.get("Email", "").strip()
            name = row.get("Name", "").strip()
            if email:
                if name:
                    contacts.append(f"{name} <{email}>")
                else:
                    contacts.append(email)
    
    output_content = args.separator.join(contacts)
    
    with open(args.output, "w", encoding="utf-8") as outfile:
        outfile.write(output_content)
    
    print(f"Email list written to {args.output}")

if __name__ == "__main__":
    main()
