import ee
from dotenv import load_dotenv
import os

load_dotenv()
ee.Initialize(project=os.getenv('GEE_PROJECT_ID'))

datasets = [
    "USGS/SRTMGL1_003",
    "ECMWF/ERA5_LAND/MONTHLY_AGGR",
    "COPERNICUS/S2_SR_HARMONIZED",
    "ESA/WorldCover/v200/2021",
    "projects/soilgrids-isric/soilgrids-2.0",
]

print("🔍 Проверка доступности датасетов:")
for ds in datasets:
    try:
        ee.Image(ds) if 'Image' in ds else ee.ImageCollection(ds)
        print(f"✅ {ds}")
    except Exception as e:
        print(f"❌ {ds}: {str(e)[:60]}")