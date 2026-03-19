import csv
import os
import reverse_geocoder as rg
import pycountry_convert as pc


def load_csv(filepath):
    """Читает CSV и возвращает список строк и заголовки."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    return rows, fieldnames


def reverse_geocode_batch(rows):
    """Выполняет пакетное обратное геокодирование для country и city."""
    coords = []

    for row in rows:
        lat = row.get("latitude")
        lon = row.get("longitude")
        if lat and lon:
            coords.append((float(lat), float(lon)))
        else:
            coords.append(None)

    valid_coords = [c for c in coords if c is not None]
    results = rg.search(valid_coords, mode=1)

    geo_results = []
    idx = 0
    for c in coords:
        if c is None:
            geo_results.append(None)
        else:
            geo_results.append(results[idx])
            idx += 1

    return geo_results


def get_continent_from_country_code(country_code):
    """Определяет континент по коду страны."""
    try:
        return pc.country_alpha2_to_continent_code(country_code)
    except KeyError:
        # специальные случаи
        if country_code == "VA":  # Vatican City
            return "EU"
        elif country_code == "XK":  # Kosovo
            return "EU"
        else:
            return ""


def enrich_data(rows):
    """Yes."""
    geo_results = reverse_geocode_batch(rows)

    for row, geo in zip(rows, geo_results):

        country_code = geo["cc"] if geo else None

        # 1) Континент добавляем всегда
        if country_code:
            row["continent"] = get_continent_from_country_code(country_code)
        else:
            row["continent"] = ""

        # 2) Если country пустой
        if not row.get("country") and geo:
            row["country"] = country_code

        # 3) Если city пустой
        if not row.get("city") and geo:
            row["city"] = geo["name"]

    return rows


def sort_data(rows):
    """Сортировка по continent -> country -> city."""
    return sorted(
        rows,
        key=lambda x: (
            x.get("continent", ""),
            x.get("country", ""),
            x.get("city", "")
        )
    )


def save_csv(filepath, rows, fieldnames):
    """Сохраняет CSV с колонкой continent в начале."""
    fieldnames = ["continent"] + fieldnames
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def add_id_column_to_csv(input_filepath, output_filepath):
    """
    Создает копию CSV файла с добавленной колонкой id в начале.
    """
    rows, fieldnames = load_csv(input_filepath)

    # Добавляем id и переупорядочиваем поля
    new_fieldnames = ["id"] + fieldnames
    for idx, row in enumerate(rows, start=1):
        row["id"] = idx

    with open(output_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    """Основная функция."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    input_file = os.path.join(script_dir, "vineyards.csv")
    output_file = os.path.join(script_dir, "vineyards_enriched.csv")
    output_file_with_id = os.path.join(script_dir, "vineyards_enriched_id.csv")

    # Флаги для отслеживания, какие файлы нужно создать
    is_enriched_exist = False
    create_enriched = True
    create_with_id = True

    # Проверяем существование vineyards_enriched.csv
    if os.path.exists(output_file):
        print(f"\nФайл {os.path.basename(output_file)} уже существует.")
        is_enriched_exist = True
        while True:
            response = input("Хотите пересоздать его? (y/n): ").strip().lower()
            if response in ['yes', 'y']:
                print("\t-> Будет пересоздан")
                create_enriched = True
                break
            elif response in ['no', 'n']:
                print("\t-> Будет пропущен")
                create_enriched = False
                break
            else:
                print("Пожалуйста, введите 'yes/y' или 'no/n'")

    # Проверяем существование vineyards_enriched_with_id.csv
    if os.path.exists(output_file_with_id):
        print(f"\nФайл {os.path.basename(output_file_with_id)} уже существует.")
        while True:
            response = input("Хотите пересоздать его? (да/нет): ").strip().lower()
            if response in ['да', 'yes', 'y', 'д']:
                print("\t-> Будет пересоздан")
                create_with_id = True
                break
            elif response in ['нет', 'no', 'n', 'н']:
                print("\t-> Будет пропущен")
                create_with_id = False
                break
            else:
                print("Пожалуйста, введите 'да' или 'нет'")

    if create_enriched is True:
        rows, fieldnames = load_csv(input_file)
        rows = enrich_data(rows)
        rows = sort_data(rows)
        save_csv(output_file, rows, fieldnames)
        is_enriched_exist = True

    # запасной с нумерацией для координации
    if (is_enriched_exist is True) and (create_with_id is True):
        add_id_column_to_csv(output_file, output_file_with_id)


if __name__ == "__main__":
    main()
