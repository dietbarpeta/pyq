import requests
from bs4 import BeautifulSoup
import os
import json
from pdf2image import convert_from_path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

BASE = "https://www.assamboard.com"
MAIN = "https://www.assamboard.com/assam-deled.html"

ROOT_FOLDER = "pdf"
API_FILE = "api/pdf.json"

os.makedirs(ROOT_FOLDER, exist_ok=True)
os.makedirs("api", exist_ok=True)

# load existing api
if os.path.exists(API_FILE):

    with open(API_FILE, "r") as f:
        api = json.load(f)

else:

    api = {"total":0,"years":{}}

existing_files = set()

for y in api["years"]:

    for item in api["years"][y]:

        existing_files.add(item["file"])


# collect paper pages
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

print("Found pages:",len(pages))


def process(page):

    try:

        r = requests.get(page,timeout=30)
        soup = BeautifulSoup(r.text,"html.parser")

        pdf_tag = soup.find("a",id="pyq-hide-1s")

        if not pdf_tag:
            return None

        pdf_link = pdf_tag["href"]

        if not pdf_link.startswith("http"):
            pdf_link = BASE + "/papers/" + pdf_link

        filename = pdf_link.split("/")[-1]

        if filename in existing_files:

            print("Skip duplicate:",filename)
            return None


        parts = filename.split("-")

        class_name = f"{parts[0]}-{parts[1]}-{parts[2]}"
        year = parts[-1].replace(".pdf","")

        title = filename.replace(".pdf","").replace("-"," ").title()

        year_path = os.path.join(ROOT_FOLDER,year)
        class_path = os.path.join(year_path,class_name)

        os.makedirs(class_path,exist_ok=True)

        save_path = os.path.join(class_path,filename)

        print("Downloading:",filename)

        data = requests.get(pdf_link,timeout=30).content

        temp_pdf = "temp.pdf"

        with open(temp_pdf,"wb") as f:
            f.write(data)

        images = convert_from_path(temp_pdf)

        pngs = []

        for i,img in enumerate(images):

            p = f"temp_{i}.png"
            img.save(p,"PNG")
            pngs.append(p)

        imgs = [Image.open(p).convert("RGB") for p in pngs]

        imgs[0].save(
            save_path,
            save_all=True,
            append_images=imgs[1:]
        )

        os.remove(temp_pdf)

        for p in pngs:
            os.remove(p)

        print("Saved:",filename)

        return {
            "year":year,
            "data":{
                "title":title,
                "file":filename,
                "class":class_name,
                "url":save_path.replace("\\","/"),
                "source":pdf_link
            }
        }

    except Exception as e:

        print("Error:",page,e)
        return None


new_items = []

with ThreadPoolExecutor(max_workers=6) as executor:

    results = executor.map(process,pages)

    for r in results:
        if r:
            new_items.append(r)


for item in new_items:

    year = item["year"]

    if year not in api["years"]:
        api["years"][year] = []

    api["years"][year].append(item["data"])


api["total"] += len(new_items)


with open(API_FILE,"w") as f:
    json.dump(api,f,indent=2)


print("Added:",len(new_items))
print("Done")
