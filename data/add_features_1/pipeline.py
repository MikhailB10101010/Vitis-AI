from services.terrain_GEE_USGS import terrain_GEE_USGS

import ee
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


ee.Authenticate()
ee.Initialize(project=os.getenv('GEE_PROJECT_ID'))

lat = 56.728766
lon = 60.587326

ans = terrain_GEE_USGS(lat, lon=lon, verbose=True)
print(ans)
