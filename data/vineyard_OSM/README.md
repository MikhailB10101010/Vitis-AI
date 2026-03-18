
# OpenStreetMap

Тест с воровством landuse=vineyard

```
project/
│
├── data/
│   ├── input.csv
│   ├── output.csv
│   └── osm/
│       └── europe-latest.osm.pbf
│
├── cache/
│   └── cache.db  # sqlite или cache.json
│
├── src/
│   ├── loader.py
│   ├── osm_local_client.py
│   ├── overpass_client.py
│   ├── vineyard_detector.py
│   ├── cache.py
│   ├── processor.py
│
└── main.py
```

## Файлы

OpenStreetMap Data Extracts - https://download.geofabrik.de

| Sub Region | .osm.pbf | .shp.zip |
| :--- | :--- | :--- |
| **Africa** | [.osm.pbf] (7.1 GB) | not available |
| **Antarctica** | [.osm.pbf] (31.5 MB) | [.shp.zip] |
| **Asia** | [.osm.pbf] (14.6 GB) | not available |
| **Australia and Oceania** | [.osm.pbf] (1.4 GB) | not available |
| **Central America** | [.osm.pbf] (731 MB) | not available |
| **Europe** | [.osm.pbf] (31.7 GB) | not available |
| **North America** | [.osm.pbf] (17.5 GB) | not available |
| **South America** | [.osm.pbf] (3.6 GB) | not available |


