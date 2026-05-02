# pipeline для заполнения датасета
# Папка с функциями
from services.terrain_GEE_USGS import terrain_GEE_USGS

# Папка по работе с БД
import db.repository as repository

# Библиотеки
import time
from pathlib import Path
import ee
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Запуск GEE
ee.Authenticate()
ee.Initialize(project=os.getenv('GEE_PROJECT_ID'))

# Настройки
BATCH_SIZE = 1000
SLEEP_TIME = 0.5

# Путь к БД
db_folder_path = Path(__file__).resolve().parent / "data"
db_folder_path.mkdir(exist_ok=True)
db_name = 'vineyard_1.db'
db_path = db_folder_path / db_name


def run_pipeline():
    total_processed = 0

    # terrain_GEE_USGS
    # 'elevation_GEE_USGS_30m'
    while True:
        cycle_processed = 0
        # Запрос из БД
        pending_items = repository.get_row_by_status(db_path, "elevation_GEE_USGS_30m", limit=BATCH_SIZE)

        # Проверка что данные еще есть
        if not pending_items:
            print("Для terrain_GEE_USGS больше нету не заполненных данных. Выход.")
            break
        else:
            cycle_processed += len(pending_items)
            total_processed += cycle_processed

        # Подгонка данных для функций
        osm_id = [item[0] for item in pending_items]
        coords = [list(item[1:]) for item in pending_items]
        features = create_feature_GEE(coords)

        #
        data_to_db = terrain_GEE_USGS(features, verbose=True)

        #
        if repository.update_vineyard_features(db_path, osm_id, data_to_db):
            print(f"{len(osm_id)}\t-\tданных загружено")

        time.sleep(SLEEP_TIME)
        # break


def create_feature_GEE(coords: list):
    return ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lon, lat])) for lat, lon in coords])


if __name__ == "__main__":
    run_pipeline()
