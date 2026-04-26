# Pipeline по вытаскиванию и обработки датасета

В подпапках могут находиться еще `README.md`

1. **[extracts_osm_py](extracts_osm_py)** → [main.py](extracts_osm_py/main.py)
    - .pbf → .geojson
    - Должны быть скачены файлы .pbf в папке [source_file](source_file) (в скрипте стоит просмотр всех подпапок с поиском по .pbf файлам)
    - Прогресс сохраняется в [extracts_osm_py](extracts_osm_py) / [results](extracts_osm_py/results)
    - Фильтрация не производиться (если не ошибаюсь), чистые исходники
    - Для "удобного" скачивания .pbf есть [download_pbf](download_pbf)

2. [extracts_osm_py](extracts_osm_py) / **[results_combine](extracts_osm_py/results_combine)** → [many_geojson_to_one.py](extracts_osm_py/results_combine/many_geojson_to_one.py)
   - many .geojson → one .geojson
   - Исходные данные [extracts_osm_py](extracts_osm_py) / [results](extracts_osm_py/results)
   - Выходные данные [extracts_osm_py](extracts_osm_py) / [results_combine](extracts_osm_py/results_combine)
   - Базовая фильтрация, включены след. признаки:
    <details>
       <summary>Часть кода, сохраняемые поля в новый .geojson</summary>
    
       ```python
       essential_columns = [
           'osm_id',  # уникальный идентификатор
           'osm_type',  # тип объекта (way/relation)
           'name',  # название
           'landuse',  # тип землепользования (должен быть vineyard)
           'geometry'  # геометрия объекта
       ]
    
       vineyard_specific = [
           'grape_variety',  # сорт винограда
           'vine_row_orientation',  # ориентация рядов
           'vine_row_direction',  # направление рядов
           'crop',  # культура
           'produce',  # производимая продукция
           'plantation',  # плантация/насаждение
           'vineyard:class',  # класс виноградника
           'vineyard:locality',  # местность/апелласьон
           'vineyard:soil',  # тип почвы
           'vineyard:village',  # деревня/село
           'vineyard:type',  # тип виноградника
           'vineyard:description:it',  # описание (итальянские регионы)
           'wine:label',  # винная этикетка/бренд
           'wine:region',  # винный регион
           'harvest_year_start',  # год начала сбора
           'harvest_first_year',  # первый год сбора
           'organic',  # органическое земледелие
           'irrigation',  # орошение
           'irrigation:water_supply',  # источник воды для орошения
           'terraced'  # террасирование
       ]
       ```
    </details>

    -
3. ~~~
   
4. [add_properties_to_geojson](add_properties_to_geojson) → **[add_geo_location_features.py](add_properties_to_geojson/add_geo_location_features.py)**
   - Для офлайн работы был использован .gpkg файл (границы стран и т.п.)
     - [natural_earth_vector](../natural_earth_vector) / [README.md](../natural_earth_vector/README.md)
   - Добавление параметров `country` и `continent`
   - Исходные данные [results_combine](extracts_osm_py/results_combine) / [merged.geojson](extracts_osm_py/results_combine/merged.geojson)
   - Выходные данные [add_properties_to_geojson](add_properties_to_geojson) / [vineyards_enriched_location.geojson](add_properties_to_geojson/vineyards_enriched_location.geojson)
