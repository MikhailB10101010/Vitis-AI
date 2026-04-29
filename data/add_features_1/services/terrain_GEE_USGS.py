# terrain_GEE_USGS.py
import ee


def terrain_GEE_USGS(
        input_data,
        lon=None,
        scale=30,
        verbose=False
):
    """
    Получает данные рельефа (высота, уклон, экспозиция) из датасета USGS/SRTMGL1_003.
    'elevation', 'slope', 'aspect', 'hillshade':.

    Args:
        input_data: Либо ee.FeatureCollection, либо широта (lat) если lon указан.
        lon=None: Долгота (если только точка).
        scale=30.

    Returns:
        Если одну точку, то на выходе будет что-то dict - {'aspect': 0, 'elevation': 260, 'hillshade': 180, 'slope': 1}.
        Если подается колекция фич (батч), то json каша
    """
    try:
        # 1 - Базовый слой (SRTM + алгоритм Terrain)
        dem = ee.Image('USGS/SRTMGL1_003')
        terrain = ee.Algorithms.Terrain(dem)    # Создает 3 канала: elevation, slope, aspect

        # 2 Ветвление от поданых данных
        if isinstance(input_data, ee.FeatureCollection):
            # Обработка коллекции (Batch mode)
            stats = terrain.sampleRegions(
                collection=input_data,
                scale=scale,
                geometries=False    # Отвечает за сох. гео. откуда взяты данные, подумал что нет смысла
            ).getInfo()

            return stats

        elif isinstance(input_data, float) or isinstance(input_data, int):
            # Обработка одиночной точки (lat, lon)
            lat = input_data
            if lon is None:
                raise ValueError("Для одиночной точки необходимо указать и lat, и lon")
            
            if verbose:
                print(f'Начало обработки точки:\t{lat}, {lon}', end='')

            # Не круто, что везде все по размному, футы метры и т.д
            point = ee.Geometry.Point([lon, lat])

            stats = terrain.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=scale
            ).getInfo()

            if verbose:
                print('\t- Done')

            return stats

        else:
            raise ValueError("terrain_GEE_USGS.py - input_data подан не верный формат")

    except Exception as e:
        print(f"Ошибка:\n{e}")
        return None
