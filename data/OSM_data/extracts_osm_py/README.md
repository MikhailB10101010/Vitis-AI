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

# Прогоны
<details>
<summary>V2</summary>

```commandline
Найдено 83 файлов .geojson
africa-260321.osm.geojson		 - OK	(объектов: 47123, колонок: 9)
australia-oceania-260321.osm.geojson		 - OK	(объектов: 17870, колонок: 9)
central-america-260317.osm.geojson		 - OK	(объектов: 18, колонок: 7)
south-america-260318.osm.geojson		 - OK	(объектов: 22490, колонок: 9)
afghanistan-latest.osm.geojson		 - OK	(объектов: 15, колонок: 7)
albania-latest.osm.geojson		 - OK	(объектов: 211, колонок: 7)
andorra-latest.osm.geojson		 - OK	(объектов: 16, колонок: 6)
armenia-latest.osm.geojson		 - OK	(объектов: 1019, колонок: 7)
austria-latest.osm.geojson		 - OK	(объектов: 29058, колонок: 9)
azerbaijan-latest.osm.geojson		 - OK	(объектов: 100, колонок: 7)
azores-latest.osm.geojson		 - OK	(объектов: 293, колонок: 9)
bangladesh-latest.osm.geojson		 - OK	(объектов: 1, колонок: 5)
belarus-latest.osm.geojson		 - OK	(объектов: 6, колонок: 7)
belgium-latest.osm.geojson		 - OK	(объектов: 609, колонок: 9)
bosnia-herzegovina-latest.osm.geojson		 - OK	(объектов: 1713, колонок: 7)
bulgaria-latest.osm.geojson		 - OK	(объектов: 2378, колонок: 9)
cambodia-latest.osm.geojson		 - OK	(объектов: 4, колонок: 6)
china-latest.osm.geojson		 - OK	(объектов: 765, колонок: 8)
croatia-latest.osm.geojson		 - OK	(объектов: 12070, колонок: 9)
cyprus-latest.osm.geojson		 - OK	(объектов: 1230, колонок: 9)
czech-republic-latest.osm.geojson		 - OK	(объектов: 10676, колонок: 9)
denmark-latest.osm.geojson		 - OK	(объектов: 87, колонок: 8)
estonia-latest.osm.geojson		 - OK	(объектов: 2, колонок: 7)
finland-latest.osm.geojson		 - OK	(объектов: 6, колонок: 6)
france-latest.osm.geojson		 - OK	(объектов: 218987, колонок: 11)
gcc-states-latest.osm.geojson		 - OK	(объектов: 2, колонок: 6)
georgia-latest.osm.geojson		 - OK	(объектов: 1159, колонок: 9)
germany-latest.osm.geojson		 - OK	(объектов: 57815, колонок: 9)
greece-latest.osm.geojson		 - OK	(объектов: 2111, колонок: 9)
guernsey-jersey-latest.osm.geojson		 - OK	(объектов: 5, колонок: 6)
hungary-latest.osm.geojson		 - OK	(объектов: 4999, колонок: 9)
iceland-latest.osm.geojson		 - OK	(объектов: 1, колонок: 6)
india-latest.osm.geojson		 - OK	(объектов: 63, колонок: 7)
indonesia-latest.osm.geojson		 - OK	(объектов: 79, колонок: 7)
iran-latest.osm.geojson		 - OK	(объектов: 126, колонок: 9)
iraq-latest.osm.geojson		 - OK	(объектов: 63, колонок: 8)
ireland-and-northern-ireland-latest.osm.geojson		 - OK	(объектов: 2, колонок: 6)
israel-and-palestine-latest.osm.geojson		 - OK	(объектов: 385, колонок: 8)
italy-latest.osm.geojson		 - OK	(объектов: 163154, колонок: 9)
japan-latest.osm.geojson		 - OK	(объектов: 11981, колонок: 8)
jordan-latest.osm.geojson		 - OK	(объектов: 4, колонок: 6)
kazakhstan-latest.osm.geojson		 - OK	(объектов: 28, колонок: 6)
kosovo-latest.osm.geojson		 - OK	(объектов: 1157, колонок: 8)
kyrgyzstan-latest.osm.geojson		 - OK	(объектов: 15, колонок: 6)
latvia-latest.osm.geojson		 - OK	(объектов: 22, колонок: 8)
lebanon-latest.osm.geojson		 - OK	(объектов: 29, колонок: 8)
liechtenstein-latest.osm.geojson		 - OK	(объектов: 89, колонок: 7)
lithuania-latest.osm.geojson		 - OK	(объектов: 5, колонок: 6)
luxembourg-latest.osm.geojson		 - OK	(объектов: 594, колонок: 7)
macedonia-latest.osm.geojson		 - OK	(объектов: 360, колонок: 8)
malaysia-singapore-brunei-latest.osm.geojson		 - OK	(объектов: 1, колонок: 5)
malta-latest.osm.geojson		 - OK	(объектов: 10, колонок: 8)
moldova-latest.osm.geojson		 - OK	(объектов: 13460, колонок: 8)
montenegro-latest.osm.geojson		 - OK	(объектов: 35, колонок: 7)
myanmar-latest.osm.geojson		 - OK	(объектов: 15, колонок: 6)
nepal-latest.osm.geojson		 - OK	(объектов: 2, колонок: 7)
netherlands-latest.osm.geojson		 - OK	(объектов: 197, колонок: 9)
north-korea-latest.osm.geojson		 - OK	(объектов: 2, колонок: 6)
norway-latest.osm.geojson		 - OK	(объектов: 10, колонок: 8)
pakistan-latest.osm.geojson		 - OK	(объектов: 3, колонок: 6)
philippines-latest.osm.geojson		 - OK	(объектов: 19, колонок: 7)
poland-latest.osm.geojson		 - OK	(объектов: 514, колонок: 9)
portugal-latest.osm.geojson		 - OK	(объектов: 34670, колонок: 9)
romania-latest.osm.geojson		 - OK	(объектов: 3839, колонок: 9)
russia-latest.osm.geojson		 - OK	(объектов: 3524, колонок: 9)
serbia-latest.osm.geojson		 - OK	(объектов: 1526, колонок: 9)
slovakia-latest.osm.geojson		 - OK	(объектов: 3572, колонок: 9)
slovenia-latest.osm.geojson		 - OK	(объектов: 50442, колонок: 9)
south-korea-latest.osm.geojson		 - OK	(объектов: 143, колонок: 7)
spain-latest.osm.geojson		 - OK	(объектов: 85287, колонок: 9)
sri-lanka-latest.osm.geojson		 - OK	(объектов: 8, колонок: 6)
sweden-latest.osm.geojson		 - OK	(объектов: 32, колонок: 7)
switzerland-latest.osm.geojson		 - OK	(объектов: 8844, колонок: 9)
syria-latest.osm.geojson		 - OK	(объектов: 20, колонок: 6)
taiwan-latest.osm.geojson		 - OK	(объектов: 2, колонок: 6)
tajikistan-latest.osm.geojson		 - OK	(объектов: 18, колонок: 6)
thailand-latest.osm.geojson		 - OK	(объектов: 15, колонок: 7)
turkey-latest.osm.geojson		 - OK	(объектов: 2524, колонок: 9)
turkmenistan-latest.osm.geojson		 - OK	(объектов: 6, колонок: 6)
ukraine-latest.osm.geojson		 - OK	(объектов: 5639, колонок: 9)
united-kingdom-latest.osm.geojson		 - OK	(объектов: 910, колонок: 9)
uzbekistan-latest.osm.geojson		 - OK	(объектов: 351, колонок: 8)
yemen-latest.osm.geojson		 - OK	(объектов: 3, колонок: 6)

Объединение файлов...

Удаление spatial-дубликатов (advanced)...
Обработка объектов: 100%|██████████| 800687/800687 [07:01<00:00, 1900.36it/s]
Удалено объектов: 2239

Результат объединения:
  - Всего объектов: 798448 (До удаления дубликатов и прочего: 826638)
  - Количество колонок: 10 (Подано в функцию: 10)
  - Колонки: ['osm_id', 'osm_type', 'name', 'landuse', 'geometry', 'grape_variety', 'crop', 'produce', 'wine:label', 'wine:region']

```

</details>