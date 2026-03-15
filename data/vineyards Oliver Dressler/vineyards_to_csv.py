import os
import json
import csv


def load_json(path):
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_region(region):
    """Split region into city and country."""
    parts = region.split(',')

    city = parts[0].strip() if len(parts) > 0 else ''
    country = parts[1].strip() if len(parts) > 1 else ''

    return normalize_value(city), normalize_value(country)


def normalize_value(value):
    """Replace unknown or None with empty string."""
    if value is None:
        return ''

    if isinstance(value, str) and value.lower() == 'unknown':
        return ''

    return value


def format_extra(extra):
    """Convert extra array to semicolon-separated string."""
    if not extra:
        return ''

    return ';'.join(str(x) for x in extra)


def extract_rows(data):
    """Extract rows for CSV."""
    rows = []

    for region, region_data in data.items():

        city, country = parse_region(region)

        vineyards = region_data.get("vineyards", [])

        for vineyard in vineyards:

            latitude = vineyard[0]
            longitude = vineyard[1]
            name = normalize_value(vineyard[2])
            website = normalize_value(vineyard[3])
            extra = format_extra(vineyard[4])

            rows.append([
                country,
                city,
                name,
                latitude,
                longitude,
                website,
                extra
            ])

    return rows


def write_csv(path, rows):
    """Write rows to CSV file."""
    header = [
        "country",
        "city",
        "name",
        "latitude",
        "longitude",
        "website",
        "extra"
    ]

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        writer.writerow(header)
        writer.writerows(rows)


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))

    json_path = os.path.join(script_dir, 'vineyards.json')
    csv_path = os.path.join(script_dir, 'vineyards.csv')

    data = load_json(json_path)

    rows = extract_rows(data)

    write_csv(csv_path, rows)


if __name__ == "__main__":
    main()
