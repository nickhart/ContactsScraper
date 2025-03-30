#!/usr/bin/env python3
import argparse
import mailbox
import re
import pandas as pd
from email.utils import getaddresses, parsedate_to_datetime
from datetime import datetime
from collections import Counter

# SQLAlchemy imports for database operations
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define domains and patterns for categorization
PERSONAL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "aol.com", "me.com", "icloud.com",
    "comcast.net", "outlook.com", "msn.com", "live.com", "mac.com", 
    "centurylink.net", "earthlink.net", "frontiernet.net", "drizzle.com",
    "verizon.net", "yahoo.co.uk", "sbcglobal.net"
}

LISTSERV_HEADERS = [
    "list-unsubscribe", "precedence", "x-mailer", "x-list"
]

AUTOMATION_KEYWORDS = ["noreply", "no-reply", "donotreply", "mailer-daemon"]

# Helper to guess name from email
def name_from_email(email):
    local_part = email.split("@")[0]
    name_parts = re.split(r'[._\-]+', local_part)
    return " ".join(part.capitalize() for part in name_parts if part.isalpha())

# Helper to parse a name string into first, last, and full name
def parse_name(raw_name, email):
    if raw_name and raw_name.strip():
        name = raw_name.strip()
        parts = name.split()
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:]), name
        else:
            return parts[0], "", name
    else:
        fallback = name_from_email(email)
        return "", "", fallback

def categorize_email(email, markers):
    domain = email.split('@')[-1].lower()
    marker_set = set(markers.split(',')) if markers else set()

    if domain in PERSONAL_DOMAINS:
        return 'personal'
    elif 'direct' in marker_set and not marker_set.intersection({'listserv', 'unsubscribe'}):
        return 'personal'
    elif 'listserv' in marker_set or 'unsubscribe' in marker_set:
        return 'listserv'
    else:
        return 'business'

# Setup SQLAlchemy database
Base = declarative_base()

class MboxOccurrence(Base):
    __tablename__ = 'mbox_occurrences'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    name = Column(String, nullable=True)  # fallback if first/last not parsed
    header_context = Column(String, nullable=False)  # e.g., "From" or "To"
    occurrence_date = Column(DateTime, nullable=True)
    markers = Column(String, nullable=True)  # e.g., "listserv,automated"
    raw_headers = Column(Text, nullable=True)

class VCFContact(Base):
    __tablename__ = 'vcf_contacts'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, index=True, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    name = Column(String, nullable=True)  # fallback if first/last not parsed

def get_session(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

# Function to ingest an MBOX occurrence into the database
def ingest_mbox_occurrence(email, first_name, last_name, full_name, header_context, occurrence_date, markers, raw_headers, session, occurrences_list):
    occurrence = MboxOccurrence(
        email=email,
        first_name=first_name,
        last_name=last_name,
        name=full_name,
        header_context=header_context,
        occurrence_date=occurrence_date,
        markers=markers,
        raw_headers=raw_headers
    )
    occurrences_list.append(occurrence)
    session.add(occurrence)

# Process a single mbox file and insert occurrences into the database
def process_mbox(mbox_path, args, session):
    mbox = mailbox.mbox(mbox_path)
    email_counter = Counter()
    interactions = {}  # {(owner_email, candidate_email): {'owner_sent': bool, 'candidate_sent': bool}}

    for msg in mbox:
        headers = msg.keys()
        msg_headers_lower = [h.lower() for h in headers]
        date_header = msg.get("Date")
        try:
            msg_date = parsedate_to_datetime(date_header) if date_header else None
            if msg_date and msg_date.tzinfo is not None:
                msg_date = msg_date.astimezone(tz=None).replace(tzinfo=None)  # Convert to naive local time
        except Exception:
            msg_date = None

        # Compute markers based on message headers
        markers_list = []
        for h in LISTSERV_HEADERS:
            if h in msg_headers_lower:
                markers_list.append("listserv")
                break  # once found, no need to add multiple times
        
        # raw_headers: comma-separated list of header keys in lower-case
        raw_headers_str = ",".join(msg_headers_lower)
        
        fields = ["From", "To"]
        
        for field in fields:
            if field in msg:
                addresses = getaddresses([msg[field]])
                for raw_name, email in addresses:
                    email = email.lower().strip()
                    if not email or "@" not in email:
                        continue
                    
                    # Count occurrences of each email for owner identification
                    email_counter[email] += 1
                    
                    # Track interactions
                    if email not in interactions:
                        interactions[email] = {'owner_sent': False, 'candidate_sent': False}

                    # If the message sender is the owner email, set 'owner_sent': True for all recipient emails
                    if field == "From":
                        interactions[email]['owner_sent'] = True
                    # If the owner email is in recipients, set 'candidate_sent': True for the sender email
                    elif field == "To":
                        interactions[email]['candidate_sent'] = True

                    # Compute additional markers based on email automation keywords
                    if any(kw in email for kw in AUTOMATION_KEYWORDS):
                        markers_list.append("automated")
                    markers_str = ",".join(set(markers_list)) if markers_list else ""
                    
                    # Parse name
                    first_name, last_name, full_name = parse_name(raw_name, email)
                    
                    # Use the current field as the header context
                    header_context = field.lower()
                    
                    # Ingest occurrence
                    ingest_mbox_occurrence(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        full_name=full_name,
                        header_context=header_context,
                        occurrence_date=msg_date,
                        markers=markers_str,
                        raw_headers=raw_headers_str,
                        session=session,
                        occurrences_list=[]
                    )
    
    # Determine the owner's email (most common email)
    owner_email = email_counter.most_common(1)[0][0] if email_counter else None

    # Add "direct" marker for bidirectional interactions
    for email, interaction in interactions.items():
        if interaction['owner_sent'] and interaction['candidate_sent']:
            for occurrence in session.query(MboxOccurrence).filter_by(email=email).all():
                occurrence.markers = (occurrence.markers + ",direct") if occurrence.markers else "direct"

    session.commit()

# Functions for VCF ingestion

def parse_vcf_card(card_lines):
    """
    Given a list of lines corresponding to a single VCF card (between BEGIN:VCARD and END:VCARD),
    parse out the email, names, etc.
    """
    contact = {
        "email": None,
        "first_name": "",
        "last_name": "",
        "name": ""
    }
    for line in card_lines:
        line = line.strip()
        if line.startswith("EMAIL"):
            # e.g., EMAIL;TYPE=INTERNET:john.doe@gmail.com
            parts = line.split(":")
            if len(parts) > 1:
                contact["email"] = parts[1].strip()
        elif line.startswith("N:"):
            # N:Last;First;Additional;... (fields separated by ;)
            parts = line[2:].split(";")
            if len(parts) >= 2:
                contact["last_name"] = parts[0].strip()
                contact["first_name"] = parts[1].strip()
                contact["name"] = f"{contact['first_name']} {contact['last_name']}".strip()
        elif line.startswith("FN:"):
            # FN:Full Name
            fn = line[3:].strip()
            if not contact["name"]:
                contact["name"] = fn
            if not contact["first_name"] and not contact["last_name"]:
                # Fallback: try splitting the full name
                parts = fn.split()
                if len(parts) >= 2:
                    contact["first_name"] = parts[0]
                    contact["last_name"] = " ".join(parts[1:])
                else:
                    contact["first_name"] = fn
    return contact

def ingest_vcf_file(vcf_path, session):
    """
    Reads a VCF file, parses individual vCards, and ingests contacts into the database.
    """
    with open(vcf_path, "r", encoding="utf-8") as f:
        card_lines = []
        in_card = False
        for line in f:
            line = line.strip()
            if line.upper() == "BEGIN:VCARD":
                in_card = True
                card_lines = []
            elif line.upper() == "END:VCARD":
                in_card = False
                contact_data = parse_vcf_card(card_lines)
                email = contact_data.get("email")
                if email:
                    # Create a new VCFContact record
                    vcf_contact = VCFContact(
                        email=email.lower(),
                        first_name=contact_data.get("first_name"),
                        last_name=contact_data.get("last_name"),
                        name=contact_data.get("name") or name_from_email(email)
                    )
                    # Check if a contact with the same email already exists and update if found, otherwise add new contact
                    existing = session.query(VCFContact).filter_by(email=vcf_contact.email).first()
                    if existing:
                        existing.name = vcf_contact.name
                        existing.first_name = vcf_contact.first_name
                        existing.last_name = vcf_contact.last_name
                    else:
                        session.add(vcf_contact)
            elif in_card:
                card_lines.append(line)
        session.commit()

def ingest_csv_contacts(csv_path, session):
    """
    Reads a CSV file of contacts (with columns for email, first_name, last_name, and name),
    and ingests them into the database (table VCFContact). It de-dupes based on email,
    and for each contact, if a field is empty in the existing record, it will be updated with the
    non-empty value from the CSV. Otherwise, existing non-empty values are preserved.
    """
    df = pd.read_csv(csv_path)
    # Normalize email column to lower-case; assume column name is 'Email' or 'email'
    if 'Email' in df.columns:
        df['email'] = df['Email'].str.lower()
    elif 'email' in df.columns:
        df['email'] = df['email'].str.lower()
    else:
        print(f"CSV {csv_path} does not contain an 'Email' column.")
        return
    
    # Standardize column names for first_name, last_name, and name
    # Look for possible variants
    def get_field(row, field_names):
        for name in field_names:
            if name in row and pd.notna(row[name]):
                value = str(row[name]).strip()
                if value:
                    return value
        return ""
    
    for index, row in df.iterrows():
        email = row['email']
        first_name = get_field(row, ['first_name', 'First', 'first'])
        last_name = get_field(row, ['last_name', 'Last', 'last'])
        name_field = get_field(row, ['name', 'Name'])
        
        # If name_field is empty but first and last exist, combine them
        if not name_field and (first_name or last_name):
            name_field = (first_name + " " + last_name).strip()
        
        # Query existing contact
        from mbox_contact_summary import VCFContact
        existing = session.query(VCFContact).filter_by(email=email).first()
        if existing:
            # For each field, if existing is empty and new value is non-empty, update it
            if not existing.first_name and first_name:
                existing.first_name = first_name
            if not existing.last_name and last_name:
                existing.last_name = last_name
            if not existing.name and name_field:
                existing.name = name_field
        else:
            # Create a new VCFContact record
            from mbox_contact_summary import name_from_email
            new_contact = VCFContact(
                email=email,
                first_name=first_name,
                last_name=last_name,
                name=name_field or name_from_email(email)
            )
            session.add(new_contact)
    session.commit()

# Main function with argparse
def main():
    parser = argparse.ArgumentParser(description="Process MBOX and VCF/CSV files and store occurrences in an SQLite database.")
    parser.add_argument("mbox_files", nargs="*", help="Paths to MBOX files")
    parser.add_argument("--vcf", nargs="*", help="Paths to VCF files")
    parser.add_argument("--csv", nargs="*", help="Paths to CSV contact files")
    parser.add_argument("--db", default="contacts.db", help="SQLite database file (default: contacts.db)")
    args = parser.parse_args()
    
    # Create or open the SQLite database using the provided filename
    session = get_session(args.db)
    
    # Process CSV contact files first
    if args.csv:
        for csv_path in args.csv:
            print(f"Processing CSV contacts file: {csv_path}...")
            ingest_csv_contacts(csv_path, session)
    
    # Process each MBOX file and ingest data into the database
    for mbox_path in args.mbox_files:
        print(f"Processing MBOX file: {mbox_path}...")
        process_mbox(mbox_path, args, session)
    
    # Process each VCF file and ingest contacts into the database
    if args.vcf:
        for vcf_path in args.vcf:
            print(f"Processing VCF file: {vcf_path}...")
            ingest_vcf_file(vcf_path, session)
    
    print(f"✅ Done! Data stored in {args.db}")

if __name__ == "__main__":
    main()