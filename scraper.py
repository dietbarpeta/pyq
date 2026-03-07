import requests
from bs4 import BeautifulSoup
import os
from pdf2image import convert_from_path
from PIL import Image

BASE = "https://www.assamboard.com"
MAIN = "https://www.assamboard.com/assam-deled.html"

ROOT_FOLDER = "pdf"
os.makedirs(ROOT_FOLDER, exist_ok=True)

res = requests.get(MAIN)
soup = BeautifulSoup(res.text, "html.parser")

pages = []

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

        temp_pdf = "temp.pdf"

        with open(temp_pdf, "wb") as f:
            f.write(data)

        print("Converting PDF → PNG")

        images = convert_from_path(temp_pdf)

        png_files = []

        for i, img in enumerate(images):

            png = f"temp_{i}.png"
            img.save(png, "PNG")
            png_files.append(png)

        print("Converting PNG → PDF")

        imgs = [Image.open(p).convert("RGB") for p in png_files]

        imgs[0].save(
            save_path,
            save_all=True,
            append_images=imgs[1:]
        )

        os.remove(temp_pdf)

        for p in png_files:
            os.remove(p)

        print("Saved:", save_path)

    except Exception as e:

        print("Error:", page, e)

print("Scraping completed.")
