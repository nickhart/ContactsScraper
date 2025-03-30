
# MBOX Contact Summary Tool

This Python script extracts and summarizes contacts from one or more `.mbox` email archive files. It outputs a CSV file containing:

- Name (from email headers or VCF)
- Email address
- Number of interactions (sent/received)
- First and last message dates
- Categorization: Personal, Business, Listserv

## ✅ Features

- Supports **multiple MBOX input files**
- Outputs a **combined CSV**
- Supports a plaintext **allowlist of known personal email addresses**
- Cross-references with optional VCF (via ChatGPT enrichment step)
- Lightweight, fast, and runs locally (no dependencies except Python 3)

## 🧪 Example Usage

```bash
python3 mbox_contact_summary.py inbox1.mbox inbox2.mbox -o contacts.csv --cc --bcc --allowlist allowlist.txt
```

> Note: `Bcc` headers are usually not present in standard MBOX exports, but if they are included, this flag ensures they're parsed.

- `--allowlist allowlist.txt`: Optional file with one email per line (whitelisted as Personal)
- `--cc` — Include email addresses from the CC field
- `--bcc` — Include email addresses from the BCC field (if available in the MBOX)

## 📦 Output Format

The script creates a CSV with:

| First Name | Last Name | Name | Email | Category | First Seen | Last Seen | Interaction Count |
|------------|-----------|------|-------|----------|------------|-----------|-------------------|

## 🧠 How Categorization Works

- `Personal`: Free domains (e.g. Gmail, Yahoo) or allowlisted
- `Business`: Company domains or unknown types
- `Listserv`: Detected by headers like `List-Unsubscribe`, or automation patterns (`noreply`, etc.)

## 🛠️ Installation

No installation needed. Just place the script and `.mbox` files in the same directory or provide full paths.

## 🔎 Using with ChatGPT (Optional)

After generating the CSV, you can upload it to ChatGPT for:

- **Further enrichment from a VCF file** (name, cross-referencing)
- **Filtering by category or frequency**
- **Merging with other contact exports**
- **Preparing a contact import file (e.g. Apple Contacts, CRM)**

### 🧪 Sample Prompts for ChatGPT

- "Here's my `contact_summary.csv`. Can you cross-reference with this VCF file and fill in names?"
- "Please split names into first and last columns if they aren't already."
- "Can you filter this contact list to just personal emails with more than 5 interactions?"
- "Generate two CSVs: one for Business and one for Personal contacts."

## 📁 Sample Files

- `mock_test_sample.mbox`: Minimal test file
- `comprehensive_mock_test.mbox`: Full test for personal, business, and listserv cases

## 🧹 Optional Improvements

- Skip low-frequency contacts (e.g. only 1 message)
- Export to SQLite or JSON
- Add CLI filtering and thresholds

---

**Author:** Nicholas Hart  
**Maintainer:** ChatGPT (assisted)
