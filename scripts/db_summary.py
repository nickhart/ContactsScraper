#!/usr/bin/env python3
import argparse
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text

# Define a base for our models
Base = declarative_base()

# Define the MboxOccurrence model matching our ingestion script
class MboxOccurrence(Base):
    __tablename__ = 'mbox_occurrences'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    name = Column(String, nullable=True)  # fallback if first/last not parsed
    header_context = Column(String, nullable=False)  # e.g., "From" or "To,CC"
    occurrence_date = Column(DateTime, nullable=True)
    markers = Column(String, nullable=True)  # e.g., "listserv,automated"
    raw_headers = Column(Text, nullable=True)

def main():
    parser = argparse.ArgumentParser(description="Summarize the contacts database.")
    parser.add_argument("db", nargs="?", default="contacts.db", help="SQLite database file (default: contacts.db)")
    args = parser.parse_args()
    
    # Connect to the SQLite database using the provided filename
    engine = create_engine(f"sqlite:///{args.db}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Query total count of MBOX occurrences
    total_occurrences = session.query(MboxOccurrence).count()
    
    # Count distinct email addresses captured
    distinct_emails = session.query(MboxOccurrence.email).distinct().count()
    
    # Find the earliest and latest occurrence dates (if available)
    min_date = session.query(func.min(MboxOccurrence.occurrence_date)).scalar()
    max_date = session.query(func.max(MboxOccurrence.occurrence_date)).scalar()
    
    # Optionally, count occurrences marked with specific markers
    listserv_count = session.query(MboxOccurrence).filter(MboxOccurrence.markers.like('%listserv%')).count()
    automated_count = session.query(MboxOccurrence).filter(MboxOccurrence.markers.like('%automated%')).count()
    
    # Print a summary of the captured data
    print("Database Summary")
    print("----------------")
    print(f"Database file: {args.db}")
    print(f"Total MBOX Occurrences: {total_occurrences}")
    print(f"Distinct Email Addresses: {distinct_emails}")
    print(f"Earliest Occurrence Date: {min_date}")
    print(f"Latest Occurrence Date: {max_date}")
    print(f"Occurrences marked as listserv: {listserv_count}")
    print(f"Occurrences marked as automated: {automated_count}")
    
    session.close()

if __name__ == "__main__":
    main()