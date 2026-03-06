import requests
from bs4 import BeautifulSoup
import os
import pikepdf

BASE = "https://www.assamboard.com"
MAIN = "https://www.assamboard.com/assam-deled.html"

ROOT_FOLDER = "pdf"
os.makedirs(ROOT_FOLDER, exist_ok=True)

res = requests.get(MAIN)
soup = BeautifulSoup(res.text, "html.parser")

pages = []

# collect paper pages
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

        if os.path.exists(save_path):
            print("Skip:", filename)
            continue

        print("Downloading:", filename)

        data = requests.get(pdf_link, timeout=30).content

        temp_file = "temp.pdf"

        with open(temp_file, "wb") as f:
            f.write(data)

        try:

            # try cleaning PDF
            with pikepdf.open(temp_file) as pdf:

                pdf.docinfo = {}

                try:
                    pdf.Root.Metadata = None
                except:
                    pass

                root = pdf.Root

                if "/OpenAction" in root:
                    del root["/OpenAction"]

                if "/AA" in root:
                    del root["/AA"]

                for p in pdf.pages:
                    if "/Annots" in p:
                        del p["/Annots"]

                pdf.save(save_path, linearize=True)

        except Exception:

            # fallback: save original pdf
            print("Cleaner failed, saving original:", filename)

            os.rename(temp_file, save_path)
            temp_file = None

        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

    except Exception as e:

        print("Error:", page, e)

print("Scraping completed.")
