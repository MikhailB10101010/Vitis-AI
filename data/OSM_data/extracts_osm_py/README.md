# OSM Vineyard Extractor

Инструмент для извлечения объектов `landuse=vineyard` (виноградников) из файлов формата OSM PBF.  
Проект состоит из основного модуля `extract_vineyards.py` и конфигурационного `main.py`, который запускает обработку для заданного региона.

## Структура проекта

```
OSM_data/
├── extract_vineyards.py # Основной модуль извлечения виноградников
├── main.py # Точка входа для обработки конкретного региона
├── results/ # Выходные файлы (GeoJSON, CSV, JSON)
│ ├── example.geojson
│ └── example.txt # на данный момент создается руками, вывод их консоли
├── source_file/ # Исходные OSM PBF-файлы
│ └── example.osm.pbf
└── README.md # Документация проекта
```