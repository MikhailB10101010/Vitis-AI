# OSM Vineyard Extractor

Инструмент для извлечения объектов `landuse=vineyard` (виноградников) из файлов формата OSM PBF.  
Проект состоит из основного модуля `extract_vineyards.py` и конфигурационного `main.py`, который запускает обработку для заданного региона.

## Параметры из файлов .pbf с карт OSM 

<details>
<summary>Требуетс доработать</summary>
osm_id - id области на карте
osm_type - 
landuse - парсинг производился по этому параметру
grape_variety - вид винограда
</details>

## Структура проекта

```
OSM_data/
├── extract_vineyards.py # Основной модуль извлечения виноградников
├── main.py # Точка входа для обработки конкретного региона
├── results/ # Выходные файлы (GeoJSON, CSV, JSON)
│ └── example.geojson
│ └── example.osm.pbf
├── logs/
│ └── *.txt # Сохранил для проверки на соответсвие кол-ва vineyard
└── README.md # Документация проекта

─ source_file/ # Исходные OSM PBF-файлы, дерикторией выше
```

## Файлы geojson

В папке `results` оставлены пару .geojson в качестве примера, оставшаяся часть весит 1,2 Гб. В архиве 104 Мб

Я.Диск: https://disk.yandex.ru/d/f4sNeFLjRL4sOQ

# Я.Диск: https://disk.yandex.ru/d/BUimS476W7Vd2g