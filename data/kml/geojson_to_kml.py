import json
import simplekml


def geojson_to_kml(geojson_file, kml_file):
    """
    Преобразует GeoJSON файл в KML файл

    Args:
        geojson_file (str): путь к входному GeoJSON файлу
        kml_file (str): путь к выходному KML файлу
    """

    # Читаем GeoJSON файл
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Создаем KML объект
    kml = simplekml.Kml()

    # Обрабатываем каждый объект в GeoJSON
    features = data.get('features', [])

    for i, feature in enumerate(features):
        geometry = feature.get('geometry')
        properties = feature.get('properties', {})

        # Пропускаем объекты с пустой геометрией
        if geometry is None:
            print(f"Предупреждение: Объект {i} пропущен (geometry = null)")
            continue

        geom_type = geometry.get('type')
        coordinates = geometry.get('coordinates')

        if geom_type == 'Point':
            # Для точки
            lon, lat = coordinates[:2]
            point = kml.newpoint(name=properties.get('name', f'Point_{i}'))
            point.coords = [(lon, lat)]

            # Добавляем свойства как описание
            if properties:
                point.description = str(properties)

        elif geom_type == 'LineString':
            # Для линии
            line = kml.newlinestring(name=properties.get('name', f'LineString_{i}'))
            line.coords = [(coord[0], coord[1]) for coord in coordinates]

            if properties:
                line.description = str(properties)

        elif geom_type == 'Polygon':
            # Для полигона
            poly = kml.newpolygon(name=properties.get('name', f'Polygon_{i}'))
            poly.outerboundaryis = [(coord[0], coord[1]) for coord in coordinates[0]]

            if properties:
                poly.description = str(properties)

        elif geom_type == 'MultiPoint':
            # Для нескольких точек
            for j, coord in enumerate(coordinates):
                point = kml.newpoint(name=properties.get('name', f'MultiPoint_{i}_{j}'))
                point.coords = [(coord[0], coord[1])]

        elif geom_type == 'MultiLineString':
            # Для нескольких линий
            for j, line_coords in enumerate(coordinates):
                line = kml.newlinestring(name=properties.get('name', f'MultiLineString_{i}_{j}'))
                line.coords = [(coord[0], coord[1]) for coord in line_coords]

        elif geom_type == 'MultiPolygon':
            # Для нескольких полигонов
            for j, poly_coords in enumerate(coordinates):
                poly = kml.newpolygon(name=properties.get('name', f'MultiPolygon_{i}_{j}'))
                poly.outerboundaryis = [(coord[0], coord[1]) for coord in poly_coords[0]]

        elif geom_type == 'GeometryCollection':
            # Для коллекции геометрий
            geometries = geometry.get('geometries', [])
            for j, geom in enumerate(geometries):
                if geom.get('type') == 'Point':
                    coords = geom.get('coordinates')
                    point = kml.newpoint(name=properties.get('name', f'GeomCollection_{i}_{j}'))
                    point.coords = [(coords[0], coords[1])]

        else:
            print(f"Предупреждение: Неподдерживаемый тип геометрии '{geom_type}' в объекте {i}")

    # Сохраняем KML файл
    kml.save(kml_file)

    # Подсчитываем количество созданных объектов
    total_features = len(kml.features)
    print(f"KML файл успешно создан: {kml_file}")
    print(f"Создано объектов: {total_features}")


# Пример использования с обработкой ошибок
if __name__ == "__main__":
    try:
        geojson_to_kml(
    r'D:\PycharmProjects\Vitis-AI\data\OSM_data\extracts_osm_py\results\south-fed-district-krasnodar.osm.geojson',
    'south-fed-district-krasnodar.osm.kml'
    )
    except FileNotFoundError:
        print("Ошибка: Файл input.geojson не найден")
    except json.JSONDecodeError:
        print("Ошибка: Некорректный формат GeoJSON файла")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
