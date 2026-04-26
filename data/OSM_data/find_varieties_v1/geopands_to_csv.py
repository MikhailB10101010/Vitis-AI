from pathlib import Path
import geopandas as gpd

# Пути к файлам
current_path = Path(__file__).resolve().parent

input_path = current_path.parent / 'add_properties_to_geojson' / 'vineyards_enriched_location.geojson'
# output_path = Path("find_varieties_v1.csv")
output_dir = current_path
output_dir.mkdir(exist_ok=True)

# 1. Загрузка
print(f"Open: {input_path}")
gdf = gpd.read_file(input_path)
print(f'is Open')

# 2. Оставляем нужные столбцы
required_columns = ['osm_id', 'continent', 'country', 'name', 'grape_variety', 'geometry']
gdf = gdf[required_columns]

# 3. Проверка CRS
if gdf.crs is None:
    gdf = gdf.set_crs(epsg=4326)

# 4. Проекция для корректного centroid
gdf_proj = gdf.to_crs(epsg=3857)

# 5. Вычисление центроидов
centroids = gdf_proj.geometry.centroid

# 6. Обратно в WGS84
centroids = gpd.GeoSeries(centroids, crs=3857).to_crs(epsg=4326)
gdf['centroid'] = centroids

# 7. Координаты центроида
gdf['centroid_lat'] = gdf['centroid'].y
gdf['centroid_lon'] = gdf['centroid'].x

# 8. Разбиение по континентам
for continent, group in gdf.groupby('continent'):
    # защита от NaN
    continent_name = str(continent) if continent else "unknown"

    # очистка имени файла
    continent_name = continent_name.replace(" ", "_").replace("/", "_")

    output_path = output_dir / f"output_{continent_name}.csv"

    # Переводим geometry в WKT
    group = group.copy()
    group['geometry'] = group.geometry.to_wkt()
    group['centroid'] = group['centroid'].to_wkt()

    # сохранение
    group.to_csv(output_path, sep=';', index=False)

    print(f"Saved: {output_path}")