#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime
from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
from mbox_contact_summary import Base, MboxOccurrence, PERSONAL_DOMAINS


def main():
    parser = argparse.ArgumentParser(description="Process mbox_occurrences and export personal contacts CSV.")
    parser.add_argument("--db", required=True, help="Path to the SQLite database file")
    parser.add_argument("--output", default="/mnt/data/personal_contacts_export.csv", help="Path to output CSV file")
    parser.add_argument("--min-occurrences", type=int, default=0, help="Drop contacts with Occurrences <= this threshold (e.g., 2)")
    parser.add_argument("--recent-date", type=str, default=None, help="Drop contacts where the most recent contact is older than this date (YYYY-MM-DD)")
    parser.add_argument("--personal-only", action="store_true", help="Export only personal contacts")
    parser.add_argument("--min-direct", type=int, default=0, help="Drop contacts with Direct Count < this threshold (e.g., 2)")
    args = parser.parse_args()

    DB_PATH = args.db
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Calculate domain frequency for all emails in mbox_occurrences, excluding yahoogroups.com
    all_emails = session.query(MboxOccurrence.email).all()
    domain_counts = {}
    for email_tuple in all_emails:
        email = email_tuple[0].lower()
        domain = email.split("@")[ -1 ]
        if domain == "yahoogroups.com":
            continue
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    # Calculate direct marker count for each email
    direct_results = session.query(
        MboxOccurrence.email,
        func.sum(case((MboxOccurrence.markers.ilike("%direct%"), 1), else_=0)).label("direct_count")
    ).group_by(MboxOccurrence.email).all()
    direct_dict = {}
    for row in direct_results:
        direct_dict[row.email.lower()] = int(row.direct_count or 0)

    # Aggregate mbox occurrences by email
    results = session.query(
        MboxOccurrence.email,
        func.count(MboxOccurrence.id).label("occurrences"),
        func.min(MboxOccurrence.occurrence_date).label("first_occurrence"),
        func.max(MboxOccurrence.occurrence_date).label("last_occurrence")
    ).group_by(MboxOccurrence.email).all()

    rows = []
    for row in results:
        email = row.email.lower()
        occurrences = row.occurrences
        first_occurrence = row.first_occurrence
        last_occurrence = row.last_occurrence

        # Determine category based on email domain
        domain = email.split('@')[-1]
        category = "personal" if domain in PERSONAL_DOMAINS else "business"

        # Retrieve the name from the record with the earliest occurrence
        name_record = session.query(MboxOccurrence.name).filter(
            MboxOccurrence.email == email,
            MboxOccurrence.occurrence_date == first_occurrence
        ).first()
        name = name_record.name if name_record and name_record.name else ""

        # Format dates as strings
        first_occ_str = first_occurrence.strftime("%Y-%m-%d %H:%M:%S") if first_occurrence else ""
        last_occ_str = last_occurrence.strftime("%Y-%m-%d %H:%M:%S") if last_occurrence else ""

        # Look up domain frequency and direct marker count
        domain_frequency = domain_counts.get(domain, 0)
        direct_count = direct_dict.get(email, 0)

        rows.append({
            "Email": email,
            "Name": name,
            "Occurrences": occurrences,
            "First Occurrence": first_occ_str,
            "Last Occurrence": last_occ_str,
            "Category": category,
            "Domain Frequency": domain_frequency,
            "Direct Count": direct_count
        })

    # Filter rows based on personal category only if specified
    if args.personal_only:
        rows = [r for r in rows if r["Category"] == "personal"]

    # Filter by minimum number of direct counts
    if args.min_direct > 0:
        rows = [r for r in rows if r["Direct Count"] >= args.min_direct]

    # Filter rows based on min-occurrences if specified
    if args.min_occurrences > 0:
        rows = [r for r in rows if r["Occurrences"] > args.min_occurrences]

    # Filter rows based on recent-date if specified
    if args.recent_date:
        from datetime import datetime
        try:
            cutoff_date = datetime.strptime(args.recent_date, "%Y-%m-%d")
            def is_recent(r):
                if not r["Last Occurrence"]:
                    return False
                try:
                    last_date = datetime.strptime(r["Last Occurrence"], "%Y-%m-%d %H:%M:%S")
                    return last_date >= cutoff_date
                except Exception:
                    return False
            rows = [r for r in rows if is_recent(r)]
        except Exception as e:
            print(f"Error parsing recent-date: {e}")

    # Write the CSV file
    csv_path = args.output
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Email", "Name", "Occurrences", "First Occurrence", "Last Occurrence", "Category", "Domain Frequency", "Direct Count"]
        with open(args.output, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    print(f"CSV export complete. File saved to {csv_path}")


if __name__ == '__main__':
    main()