# ContactsScraper - MBOX Contact Summary Tool

## Overview
This project contains a collection of Python scripts which can extracts and summarize contacts from one or more `.mbox` email archive files. It collects information about each email address and inserts it into a database. Then a second script reads the database and attempts to categorize and filter the data, then outputs a CSV file containing:

- **Name** (extracted from email headers or optionally enriched from a VCF file)
- **Email address**
- **Number of interactions** (sent/received)
- **First and last message dates**
- **Category** (Personal, Business, Listserv)

### A note on ChatGPT

This project was one of my first experiments "vibe coding" with ChatGPT. Overall it was pretty successful, but I definitely had to make a bunch of refinements myself, and the documentation is 90% human written.

Originally I wanted to upload the MBOX files to ChatGPT but we're talking about multiple gigabytes of data. I quickly realized I needed a way to scrape as much relevant information as possible and store it in a database, which could then be uploaded and processed.

I went through numerous iterations of asking ChatGPT to detect personal email addresses and got unsatisfactory results which led me to take the script it was using to process the data and make a local copy of it. I further refined and enhanced this script myself.

## Purpose
If you have ever had to collect someone's contacts (for instance in case they are 
deceased) this tool will comb through their email and attempt to categorize each email 
address it encounters as personal, business, or a listserv. 

The `mbox_contact_summary.py` script reads the MBOX file(s) and deduces the email address of the account owner by finding the most commonly occurring email address. It iterates through each email and looks for markers that might help categorize the email (eg: "noreply" email addresses, presence of unsubscribe or other common listserv headers). Such markers, as well as the other headers are added to each record in the database.

You can also supply a supplementary VCF or CSV file of contacts to `mbox_contact_summary.py`, which will be used to cross-reference emails where only the address is pressent and no name information. This can help fill in the details of a contact that may be missing from Gmail but are present in the account holder's phone. If there's another source of data to help fill in this information you can provide it via the CSV (this is a simple {first name, last name, email} format).

The `process_db.py` script processes the entries in the contacts DB
It looks at every "to" and "from" address it finds and counts how many direct interactions there are between each candidate email address and the owner's. This "direct count" is added to the record for each candidate email address. The frequency of each email domain is also recorded, in case this is helpful for categorization or filtering purposes.

I made several iterations on the logic of these scripts and then manually reviewed the results (containing literally thousands of email addresses). By sorting and filtering the data within a spreadsheet I was able to look for miscategorized email addresses. Sometimes I would manually cross-reference an email address by searching the account holder's gmail account and verify if this was someone with whom they had direct contact or they happened to be on an email chain.

Eventually I arrived at the scripts in their current format and was able to reduce the number of candidate emails from thousands to hundreds. I used the `--min-occurrences` parameter to exclude emails with less than 3 interactions. I used `--recent-date 2021-01-01` to exclude any contact that hadn't been corresponded with since 1/1/2021. I scrutinized the "business" contacts (of which there were only a few dozen) and did find a few contacts that were using a business email address but clearly had a personal connection. Then I sorted ascending by number of interactions or by most recent interaction date, and manually checked the fewest/oldest contacts. Some of them were personal, but many seemed to be random conversations with people on listservs.

Finally I used the script `format_email_list.py` to format a list of email addresses which could be copy/pasted into an email (or distribution list). 

### The future of this project

I've taken this project about as far as I'm likely to go--it served its purpose and enabled me to send emails to a bunch of people for whom I needed to inform about the passing of someone close. I put a README in here and posted this publicly in case it is useful for others.

And if there's anyone involved in a startup for assisting with end-of-life issues, hit me up. I have some thoughts.
 
## ✅ Features

- Supports processing **multiple MBOX input files** simultaneously
- Outputs a **single combined CSV**
- Uses an optional plaintext **allowlist** to identify personal contacts
- Can integrate additional data from a **VCF file** (via ChatGPT enrichment step)
- Lightweight and runs locally with no external dependencies (only Python 3 required)

## 🧪 Example Usage

```bash
python3 mbox_contact_summary.py inbox1.mbox inbox2.mbox \
    --db contacts.db --vcf contacts.vcf --csv additional_contacts.csv
```

**Command-line options:**

- `--db`: The path to the file to output the generated contacts DB
- `--vcf contacts.vcf`: Optional VCF file containing contact information (eg: export from person's phone)
- `--csv`: Optional CSV file containing contact information (first name, last name, email)

## 🧪 Example Usage

```bash
python3 process_db.py --db contacts.db --output exported_contacts.csv \
    --min-occurrences 2 --recent-date 2021-01-01 --min-direct 1 --personal_only true
```

**Command-line options:**

- `--db contacts.db`: The path to the SQLite database containing the contacts information
- `--output exported_contacts.csv`: The path to the output CSV file for exported contacts
- `--min-occurrences N`: Optional argument to include only contacts that occur at least N times
- `--recent-date YYYY-MM-DD`: Optional argument to specify a minimum date for the most recent interaction
- `--min-direct N`: Optional argument to specify the minimum number of direct interactions with the account owner
- `--personal-only true|false`: Optional argument to specify only contacts categorized as personal should be emitted


## 📦 Output Format

| First Name | Last Name | Name | Email | Category | First Seen | Last Seen | Interaction Count |
|------------|-----------|------|-------|----------|------------|------------------------------|


## 🧠 Categorization Logic

- **Personal**: Recognized via free email domains (e.g., Gmail, Yahoo)
- **Business**: Identified through corporate or unrecognized domains not marked personal.
- **Listserv**: Detected via automation patterns (`noreply`, etc.) or email headers like `List-Unsubscribe`.

## 🛠️ Installation

No specific installation required. Ensure Python 3 is installed and place the script and your `.mbox` files in the same directory, or provide full paths. It does require the SQLAlchemy python package.

## 🔎 Optional ChatGPT Integration

For additional data enrichment, upload the generated CSV to ChatGPT to:

- Cross-reference contacts with a VCF file.
- Further filter and categorize contacts.
- Prepare data for importing into contact managers like Apple Contacts or CRM software.

### 🧪 ChatGPT Sample Prompts

- "Here's my CSV. Cross-reference it with this VCF and fill in missing names."
- "Split names into separate first and last name columns."
- "Filter contacts for personal emails with more than 5 interactions."
- "Generate separate CSVs for Business and Personal categories."

## 📁 Sample Files

- `mock_test_sample.mbox`: Minimal example file.
- `comprehensive_mock_test.mbox`: Extensive test covering multiple categories.

## How to get your MBOX and VCF files

Most big email services and ISPs offer tools to download your email data. Below are a few helpful links
- [Gmail](https://support.google.com/accounts/answer/3024190)
- [Xfinity](https://exporthelp.xfinity.com/article/692-export-your-emails-and-contacts-as-a-file)

In order to export contacts from an iOS device you can use this [Apple support article](https://support.apple.com/guide/iphone/export-contacts-iph075ddebf2/ios).

## 🧹 Possible Enhancements

- Add support for exporting data in SQLite or JSON format.
- Additional command-line filters and customization (eg: exclude automated email addresses like "noreply").

---

**Author:** Nicholas Hart  
**Maintainer:** ChatGPT (assisted)