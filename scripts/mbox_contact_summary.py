import mailbox
import csv
import email.utils
from collections import defaultdict
from datetime import datetime

# Customize these paths
mbox_file_path = "data/mock_test_sample.mbox"
output_csv_path = "contact_summary.csv"

# Dictionary to store contact frequency and name
contact_counts = defaultdict(lambda: {"name": None, "count": 0})

def extract_name_and_email(raw):
    name, addr = email.utils.parseaddr(raw)
    return name.strip() or None, addr.lower().strip()

# Read the MBOX file
print("Reading MBOX file... This may take a few minutes.")
mbox = mailbox.mbox(mbox_file_path)

for message in mbox:
    try:
        # Extract From and To fields
        from_raw = message.get("From", "")
        to_raw = message.get("To", "")

        # Extract and count sender
        name, email_addr = extract_name_and_email(from_raw)
        if email_addr:
            contact_counts[email_addr]["count"] += 1
            if not contact_counts[email_addr]["name"]:
                contact_counts[email_addr]["name"] = name

        # Extract and count recipients
        if to_raw:
            recipients = email.utils.getaddresses([to_raw])
            for r_name, r_email in recipients:
                r_email = r_email.lower().strip()
                if r_email:
                    contact_counts[r_email]["count"] += 1
                    if not contact_counts[r_email]["name"]:
                        contact_counts[r_email]["name"] = r_name.strip() or None

    except Exception as e:
        print(f"Error processing message: {e}")
        continue

# Write to CSV
print(f"Writing summary to {output_csv_path}...")
with open(output_csv_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Email", "Interaction Count"])
    for email_addr, data in sorted(contact_counts.items(), key=lambda x: x[1]["count"], reverse=True):
        writer.writerow([data["name"] or "", email_addr, data["count"]])

print("Done! You can now upload the CSV here for categorization.")
