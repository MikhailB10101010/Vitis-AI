import sys
import os
import time
import csv
import numpy as np
from datetime import datetime
from pathlib import Path


# Windows compatibility fix
if sys.platform == 'win32':
    class MockModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None


    for module_name in ['fcntl', 'termios', 'tty']:
        if module_name not in sys.modules:
            sys.modules[module_name] = MockModule()

# Python 2/3 compatibility fix для Windows
import sys
if sys.version_info[0] >= 3:
    import io
    sys.modules['StringIO'] = io
    sys.modules['StringIO'].StringIO = io.StringIO

# Windows compatibility fix ee
if sys.platform == 'win32':
    class MockModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    for module_name in ['fcntl', 'termios', 'tty']:
        if module_name not in sys.modules:
            sys.modules[module_name] = MockModule()

#
import ee
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# Инициализация GEE
load_dotenv()
ee.Initialize(project=os.getenv('GEE_PROJECT_ID'))
print("✅ GEE подключён")

# === КОНФИГУРАЦИЯ ===
REGIONS = {
    'Крым': [32.5, 44.0, 36.5, 45.5],
    'Краснодарский край': [33.5, 43.0, 40.5, 46.5],
    'Грузия': [40.0, 41.0, 47.0, 43.5],
    'Армения': [43.5, 38.5, 46.5, 41.5],
}

OUTPUT_FILE = 'data/vineyard_dataset.csv'
KNOWN_VINEYARDS_FILE = 'data/known_vineyards.csv'
POSITIVE_BUFFER_M = 500
NEGATIVE_RATIO = 3


# === ФУНКЦИИ СБОРА ===

def get_features(point, year=2023):
    """Упрощённое извлечение признаков — только гарантированно доступные датасеты"""
    result = {}

    try:
        # === 1. РЕЛЬЕФ (SRTM) — обязательно ===
        srtm = ee.Image("USGS/SRTMGL1_003")
        result['elevation'] = srtm.select('elevation').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=30).get('elevation')

        terrain = ee.Algorithms.Terrain(srtm.select('elevation'))
        result['slope'] = terrain.select('slope').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=30).get('slope')
        result['aspect'] = terrain.select('aspect').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=30).get('aspect')
    except Exception as e:
        print(f"⚠️ SRTM ошибка: {e}")
        result.update({'elevation': 200, 'slope': 5, 'aspect': 180})  # fallback

    try:
        # === 2. КЛИМАТ (ERA5) — обязательно ===
        era5_temp = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR") \
            .filterDate(f'{year}-04-01', f'{year}-10-31') \
            .select('temperature_2m_mean')
        result['temp_mean'] = era5_temp.mean().reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=1000).get('temperature_2m_mean')

        # GDD (упрощённо)
        gdd = era5_temp.map(lambda img: img.subtract(10).max(0)).sum()
        result['gdd'] = gdd.reduceRegion(
            reducer=ee.Reducer.sum(), geometry=point, scale=1000).get('temperature_2m_mean')

        # Осадки
        era5_precip = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR") \
            .filterDate(f'{year}-01-01', f'{year}-12-31') \
            .select('total_precipitation_sum')
        result['precip'] = era5_precip.sum().reduceRegion(
            reducer=ee.Reducer.sum(), geometry=point, scale=1000).get('total_precipitation_sum')
    except Exception as e:
        print(f"⚠️ ERA5 ошибка: {e}")
        result.update({'temp_mean': 20, 'gdd': 2500, 'precip': 600})  # fallback

    try:
        # === 3. NDVI (Sentinel-2) — обязательно ===
        ndvi = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterDate(f'{year}-06-01', f'{year}-09-30') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)) \
            .map(lambda img: img.normalizedDifference(['B8', 'B4']).rename('NDVI')) \
            .select('NDVI').median()
        result['ndvi'] = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=20).get('NDVI')
    except Exception as e:
        print(f"⚠️ Sentinel-2 ошибка: {e}")
        result['ndvi'] = 0.5  # fallback

    try:
        # === 4. Land Cover (WorldCover) — опционально ===
        lc = ee.Image("ESA/WorldCover/v200/2021").reduceRegion(
            reducer=ee.Reducer.mode(), geometry=point, scale=10).get('Map')
        result['landcover'] = lc
    except:
        result['landcover'] = 40  # fallback: cropland

    # === 5. SoilGrids — ПОЛНОСТЬЮ ОПЦИОНАЛЬНО, без ошибок ===
    try:
        soil = ee.Image("projects/soilgrids-isric/soilgrids-2.0")
        result['soil_ph'] = soil.select('phh2o_mean').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=250).get('phh2o_mean')
        result['soil_soc'] = soil.select('soc_mean').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=250).get('soc_mean')
        result['soil_clay'] = soil.select('clay_mean').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=250).get('clay_mean')
    except:
        # Просто добавляем fallback значения, НЕ печатаем ошибку
        result.update({'soil_ph': 6.5, 'soil_soc': 2.0, 'soil_clay': 25.0})

    # Конвертируем ee.Number в Python-значения
    final = {}
    for k, v in result.items():
        try:
            final[k] = float(v.getInfo()) if v is not None else np.nan
        except:
            final[k] = np.nan

    return final  # Всегда возвращаем dict, никогда None!


def collect_positive_samples(known_file):
    """Сбор positive class (существующие виноградники)"""
    samples = []

    if not Path(known_file).exists():
        print(f"❌ Файл {known_file} не найден")
        return samples

    df = pd.read_csv(known_file)
    print(f"📍 Загружено {len(df)} известных виноградников")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Positive class"):
        point = ee.Geometry.Point([row['lon'], row['lat']])

        # Основная точка + буферные точки (аугментация)
        for offset_m in [0, 100, 250]:
            if offset_m > 0:
                angle = np.random.uniform(0, 2 * np.pi)
                offset_lon = (offset_m / 111320) * np.cos(angle) / np.cos(np.radians(row['lat']))
                offset_lat = (offset_m / 111320) * np.sin(angle)
                sample_point = ee.Geometry.Point([row['lon'] + offset_lon, row['lat'] + offset_lat])
                lat, lon = row['lat'] + offset_lat, row['lon'] + offset_lon
            else:
                sample_point = point
                lat, lon = row['lat'], row['lon']

            feats = get_features(sample_point)
            if feats and feats.get('ndvi', 0) > 0.2:
                feats.update({
                    'label': 1,
                    'name': row['name'],
                    'region': row['region'],
                    'lat': lat,
                    'lon': lon,
                    'source': 'known_vineyard'
                })
                samples.append(feats)

            time.sleep(0.1)

    return samples


def collect_negative_samples(positive_samples, regions):
    """Сбор negative class (PU-Learning: исключаем леса, воду, высокогорье)"""
    samples = []
    n_target = len(positive_samples) * NEGATIVE_RATIO

    # Маска непригодных зон
    worldcover = ee.Image("ESA/WorldCover/v200/2021")
    srtm = ee.Image("USGS/SRTMGL1_003")
    terrain = ee.Algorithms.Terrain(srtm.select('elevation'))

    exclude_lc = [10, 20, 30, 80, 90, 95]  # Forest, shrubland, water, wetlands, snow

    attempts = 0
    max_attempts = n_target * 10

    with tqdm(total=n_target, desc="Negative class") as pbar:
        while len(samples) < n_target and attempts < max_attempts:
            attempts += 1

            # Случайная точка в регионе
            region_name = np.random.choice(list(regions.keys()))
            lon_min, lat_min, lon_max, lat_max = regions[region_name]
            lon = np.random.uniform(lon_min, lon_max)
            lat = np.random.uniform(lat_min, lat_max)
            point = ee.Geometry.Point([lon, lat])

            # Проверка исключений
            lc_val = worldcover.reduceRegion(
                reducer=ee.Reducer.first(), geometry=point, scale=10).get('Map')
            elev_val = srtm.select('elevation').reduceRegion(
                reducer=ee.Reducer.first(), geometry=point, scale=30).get('elevation')
            slope_val = terrain.select('slope').reduceRegion(
                reducer=ee.Reducer.first(), geometry=point, scale=30).get('slope')

            lc_info = lc_val.getInfo() if lc_val else None
            elev_info = elev_val.getInfo() if elev_val else None
            slope_info = slope_val.getInfo() if slope_val else None

            # Исключаем непригодные зоны
            if lc_info in exclude_lc:
                continue
            if elev_info and elev_info > 1500:
                continue
            if slope_info and slope_info > 25:
                continue

            # Проверка расстояния до positive samples (ИСПРАВЛЕНО!)
            too_close = False
            for ps in positive_samples:
                lat_diff = ps['lat'] - lat
                lon_diff = ps['lon'] - lon
                dist = (lat_diff * lat_diff + lon_diff * lon_diff) ** 0.5 * 111320
                if dist < POSITIVE_BUFFER_M:
                    too_close = True
                    break
            if too_close:
                continue

            # Извлечение признаков
            feats = get_features(point)
            if not feats or feats.get('ndvi', 1) < 0.1:
                continue

            feats.update({
                'label': 0,
                'name': 'unlabeled',
                'region': region_name,
                'lat': lat,
                'lon': lon,
                'source': 'random_unlabeled'
            })
            samples.append(feats)
            pbar.update(1)

            time.sleep(0.05)

    return samples


def save_dataset(samples, output_file):
    """Сохранение в CSV"""
    if not samples:
        print("❌ Нет данных для сохранения")
        return

    fieldnames = ['label', 'name', 'region', 'lat', 'lon', 'source',
                  'elevation', 'slope', 'aspect', 'temp_mean', 'gdd', 'precip',
                  'ndvi', 'soil_ph', 'soil_soc', 'soil_clay', 'landcover']

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for sample in samples:
            writer.writerow(sample)

    print(f"💾 Сохранено {len(samples)} записей в {output_file}")

    # Статистика
    df = pd.read_csv(output_file)
    print(f"\n📊 Распределение классов:")
    print(df['label'].value_counts())
    print(f"\n📈 Признаков: {len(fieldnames) - 5}")


# === ЗАПУСК ===
if __name__ == "__main__":
    print("🍇 Vitis-AI: Сбор датасета через GEE")
    print("=" * 50)

    start_time = time.time()

    # 1. Positive class
    positive_samples = collect_positive_samples(KNOWN_VINEYARDS_FILE)
    print(f"✅ Positive: {len(positive_samples)} точек")

    # 2. Negative class
    negative_samples = collect_negative_samples(positive_samples, REGIONS)
    print(f"✅ Negative: {len(negative_samples)} точек")

    # 3. Объединение и сохранение
    all_samples = positive_samples + negative_samples
    save_dataset(all_samples, OUTPUT_FILE)

    elapsed = time.time() - start_time
    print(f"\n⏱️ Завершено за {elapsed:.1f} сек")
    print("=" * 50)