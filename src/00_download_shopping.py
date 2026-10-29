"""Download the pinned shopping source for local reproduction only."""

# Import standard tools for downloading, checking and reading the archive.
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

# Fix the source version and fingerprint rather than silently using a new file.
ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.kaggle.com/api/v1/datasets/download/iamsouravbanerjee/customer-shopping-trends-dataset?datasetVersionNumber=2"
EXPECTED_HASH = "3e05d375388b7f74039bfeefd41405075e0b0643e1d04a77de1ed11cd1e68dd5"

# Retrieve only the public source and verify the selected file before saving it.
request = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urlopen(request, timeout=60) as response:
    archive_bytes = response.read()
with ZipFile(BytesIO(archive_bytes)) as archive:
    csv_bytes = archive.read("shopping_trends_updated.csv")
if sha256(csv_bytes).hexdigest() != EXPECTED_HASH:
    raise ValueError("Shopping source fingerprint differs from the reviewed version.")

# Save the source locally; .gitignore excludes it from the public repository.
target = ROOT / "data/raw/shopping_trends_updated.csv"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(csv_bytes)
print("Saved the verified shopping CSV locally. Source is synthetic; raw redistribution is unclear.")
