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
   - Удаление позиций обозначающих один виноградник, но с неправильной геометрией (обрезки от полного виноградника)
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
        #'vine_row_orientation',  # ориентация рядов
        #'vine_row_direction',  # направление рядов
        'crop',  # культура
        'produce',  # производимая продукция
        #'plantation',  # плантация/насаждение
        #'vineyard:class',  # класс виноградника
        #'vineyard:locality',  # местность/апелласьон
        #'vineyard:soil',  # тип почвы
        #'vineyard:village',  # деревня/село
        #'vineyard:type',  # тип виноградника
        #'vineyard:description:it',  # описание (итальянские регионы)
        'wine:label',  # винная этикетка/бренд
        'wine:region',  # винный регион
        #'harvest_year_start',  # год начала сбора
        #'harvest_first_year',  # первый год сбора
        #'organic',  # органическое земледелие
        #'irrigation',  # орошение
        #'irrigation:water_supply',  # источник воды для орошения
        #'terraced'  # террасирование
    ]
   ```

    </details>

    -
   
3. [add_properties_to_geojson](add_properties_to_geojson) → **[add_geo_location_features.py](add_properties_to_geojson/add_geo_location_features.py)**
   - Для офлайн работы был использован .gpkg файл (границы стран и т.п.)
     - [natural_earth_vector](../natural_earth_vector) / [README.md](../natural_earth_vector/README.md)
   - Добавление параметров `country` и `continent`
   - Исходные данные [results_combine](extracts_osm_py/results_combine) / [merged.geojson](extracts_osm_py/results_combine/merged.geojson)
   - Выходные данные [add_properties_to_geojson](add_properties_to_geojson) / [vineyards_enriched_location.geojson](add_properties_to_geojson/vineyards_enriched_location.geojson)


# Заметки

<details>
<summary>Ранее используемые параметры, но удаленные из-за их пустоты в OSM</summary>

```commandline
<class 'geopandas.geodataframe.GeoDataFrame'>
RangeIndex: 800687 entries, 0 to 800686
Data columns (total 27 columns):
 #   Column                   Non-Null Count   Dtype   
---  ------                   --------------   -----   
 0   osm_id                   800687 non-null  int32   
 1   osm_type                 800687 non-null  str     
 2   name                     7257 non-null    str     
 3   landuse                  800687 non-null  str     
 4   grape_variety            1529 non-null    str     
 5   vine_row_orientation     2092 non-null    str     
 6   vine_row_direction       1 non-null       str     
 7   crop                     556374 non-null  str     
 8   produce                  737 non-null     str     
 9   plantation               4 non-null       str     
 10  vineyard:class           5 non-null       str     
 11  vineyard:locality        53 non-null      str     
 12  vineyard:soil            1 non-null       str     
 13  vineyard:village         10 non-null      str     
 14  vineyard:type            9 non-null       str     
 15  vineyard:description:it  1 non-null       str     
 16  wine:label               1704 non-null    str     
 17  wine:region              153 non-null     str     
 18  harvest_year_start       1 non-null       str     
 19  harvest_first_year       3 non-null       str     
 20  organic                  124 non-null     str     
 21  irrigation               3 non-null       str     
 22  irrigation:water_supply  1 non-null       str     
 23  terraced                 84 non-null      str     
 24  country                  800687 non-null  str     
 25  continent                800687 non-null  str     
 26  geometry                 800687 non-null  geometry
dtypes: geometry(1), int32(1), str(25)
memory usage: 184.9 MB
```

</details>