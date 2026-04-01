# Pipeline

- `add_geo_location_features.py`
  - Для `*.geojson` файла добавление `country` и `continent` используя "natural_earth_vector" (`natural_earth_vector.gpkg`)
- empty

# Links

- Добавление стран и континентов в merge.geojson 
Я.Диск: https://disk.yandex.ru/d/1Dhh8zWog3MuHw

# Info

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