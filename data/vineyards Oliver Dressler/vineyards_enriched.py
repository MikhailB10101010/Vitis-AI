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


def main():
    """Основная функция."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    input_file = os.path.join(script_dir, "vineyards.csv")
    output_file = os.path.join(script_dir, "vineyards_enriched.csv")

    rows, fieldnames = load_csv(input_file)
    rows = enrich_data(rows)
    rows = sort_data(rows)
    save_csv(output_file, rows, fieldnames)


if __name__ == "__main__":
    main()
