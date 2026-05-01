# terrain_GEE_USGS.py
import ee


def terrain_GEE_USGS(
        input_data,
        lon=None,
        scale: int = 30,
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
        Если подается колекция фич (батч), то массив из dict {'aspect': 0, 'elevation': 260, 'hillshade': 180, 'slope': 1}
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

            # Структура json → в массив dict как в одиночной подаче координат
            stats = [feature['properties'] for feature in stats['features']]

            return change_key_name(stats, scale)

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

            return change_key_name(stats, scale)

        else:
            raise ValueError("terrain_GEE_USGS.py - input_data подан не верный формат")

    except Exception as e:
        print(f"Ошибка:\n{e}")
        return None


def change_key_name(
        input_dict,
        scale,
        mapping_without_Nm={'aspect': 'aspect_GEE_USGS_',
                            'elevation': 'elevation_GEE_USGS_',
                            'hillshade': 'hillshade_GEE_USGS_',
                            'slope': 'slope_GEE_USGS_'}
):
    mapping = mapping_without_Nm
    for key in mapping.keys():
        mapping[key] = mapping[key] + f"{scale}m"

    def rename_dict(d):
        return {mapping.get(k, k): v for k, v in d.items()}

    # Если на входе список, обрабатываем каждый элемент
    if isinstance(input_dict, list):
        return [rename_dict(item) for item in input_dict]

    # Если на входе один словарь, обрабатываем его
    if isinstance(input_dict, dict):
        return rename_dict(input_dict)

    # Если пришло что-то другое
    return -1
