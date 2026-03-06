import requests
from bs4 import BeautifulSoup
import os
import pikepdf

BASE = "https://www.assamboard.com"
MAIN = "https://www.assamboard.com/assam-deled.html"

ROOT_FOLDER = "pdf"
os.makedirs(ROOT_FOLDER, exist_ok=True)

# Load main page
res = requests.get(MAIN)
soup = BeautifulSoup(res.text, "html.parser")

pages = []

# Collect paper pages
for a in soup.find_all("a", href=True):

    href = a["href"]

    if "/papers/" in href and href.endswith(".html"):

        if href.startswith("http"):
            pages.append(href)
        else:
            pages.append(BASE + href)

pages = list(set(pages))

print("Found pages:", len(pages))

for page in pages:

    try:

        r = requests.get(page, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        pdf_tag = soup.find("a", id="pyq-hide-1s")

        if not pdf_tag:
            continue

        pdf_link = pdf_tag["href"]

        if not pdf_link.startswith("http"):
            pdf_link = BASE + "/papers/" + pdf_link

        filename = pdf_link.split("/")[-1]

        parts = filename.split("-")

        class_folder = f"{parts[0]}-{parts[1]}-{parts[2]}"
        year = parts[-1].replace(".pdf", "")

        year_path = os.path.join(ROOT_FOLDER, year)
        class_path = os.path.join(year_path, class_folder)

        os.makedirs(class_path, exist_ok=True)

        save_path = os.path.join(class_path, filename)

        # Skip if already exists
        if os.path.exists(save_path):
            print("Skip:", filename)
            continue

        print("Downloading:", filename)

        data = requests.get(pdf_link, timeout=30).content

        temp_file = "temp.pdf"

        try:

            # Save temp PDF
            with open(temp_file, "wb") as f:
                f.write(data)

            # Clean PDF
            with pikepdf.open(temp_file) as pdf:

                # Remove metadata
                pdf.docinfo = {}

                # Remove XMP metadata
                try:
                    pdf.Root.Metadata = None
                except:
                    pass

                root = pdf.Root

                # Remove redirect actions
                if "/OpenAction" in root:
                    del root["/OpenAction"]

                if "/AA" in root:
                    del root["/AA"]

                # Remove annotations / tracking links
                for p in pdf.pages:

                    annots = p.get("/Annots")

                    if not annots:
                        continue

                    for annot in annots:

                        try:
                            obj = annot.get_object()

                            if "/A" in obj:
                                del obj["/A"]

                            if "/URI" in obj:
                                del obj["/URI"]

                        except:
                            pass

                # Save clean PDF
                pdf.save(save_path, linearize=True)

        finally:

            if os.path.exists(temp_file):
                os.remove(temp_file)

    except Exception as e:

        print("Error:", page, e)

print("Scraping completed.")
