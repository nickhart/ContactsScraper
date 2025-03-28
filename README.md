# MBOX Contact Summary Tool

This tool extracts email contact information from an `.mbox` file and summarizes it by:
- Name
- Email address
- Number of interactions (sent or received)

The output is saved as a `.csv` file for easy review and categorization.

---

## 📁 Files
- `mbox_contact_summary.py` — The main script
- `mock_test_sample.mbox` — A small test `.mbox` file with sample messages

---

## 🛠 How to Use

### 1. Download or Clone the Script
Save `mbox_contact_summary.py` and place it in your working directory.

### 2. (Optional) Download Sample MBOX File
Use the provided test file for trial runs:
- [Download mock_test_sample.mbox](sandbox:/mnt/data/mock_test_sample.mbox)

### 3. Configure the Script
Open `mbox_contact_summary.py` and update the paths at the top:
```python
mbox_file_path = "mock_test_sample.mbox"
output_csv_path = "contact_summary.csv"
```

### 4. Run the Script
In your terminal:
```bash
cd /path/to/script
python3 mbox_contact_summary.py
```

### 5. Check the Output
The script will generate:
- `contact_summary.csv` — contains Name, Email, and Interaction Count

Open it in Excel, Numbers, or any CSV viewer.

---

## 🧪 Sample Output Format
```
Name,Email,Interaction Count
Alice Example,alice@example.com,3
Bob Example,bob@example.com,1
Charlie Work,charlie@company.com,1
newsletter@news.com,,1
```

---

## ✅ Next Steps
- Upload the resulting `.csv` here to classify contacts as **Personal** or **Business**
- You can also upload a `.vcf` file (exported iPhone contacts) to cross-reference

Let me know if you'd like filters for year, domain, or other refinements!

