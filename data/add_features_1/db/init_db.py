# init_db.py - Инициализация БД
import geopandas as gpd
from pathlib import Path

from schema import setup_database
from repository import insert_points


def load_geojson_to_db(geojson_path, db_path):
    gdf = gpd.read_file(geojson_path)

    required_attr = {"osm_id"}
    if not required_attr.issubset(gdf.columns):
        raise ValueError(f"GeoJSON должен содержать атрибут {required_attr}")

    # Извлекаем данные: id, широту и долготу из геометрии
    # geometry.y — это lat, geometry.x — это lon
    points = []
    for _, row in gdf.iterrows():
        geom = row["geometry"]
        if geom is None:
            continue

        # Если это точка — берем её координаты напрямую
        if geom.geom_type == 'Point':
            lat, lon = geom.y, geom.x
        # Если это полигон или линия — берем центр (centroid)
        else:
            centroid = geom.centroid
            lat, lon = centroid.y, centroid.x

        points.append((row["osm_id"], lat, lon))

    insert_points(points, db_path)


if __name__ == "__main__":
    # Путь к БД
    db_folder_path = Path(__file__).resolve().parent.parent / "data"
    db_folder_path.mkdir(exist_ok=True)
    db_name = 'vineyard_1.db'
    db_path = db_folder_path / db_name

    # Путь к Данным
    geojson_path = Path(__file__).resolve().parent.parent.parent / "OSM_data" / "extracts_osm_py" / "results_combine" / "merged.geojson"

    print("Создание БД...")
    setup_database(db_path)

    print("Загрузка GeoJSON...")
    load_geojson_to_db(geojson_path, db_path)

    print("Done")
