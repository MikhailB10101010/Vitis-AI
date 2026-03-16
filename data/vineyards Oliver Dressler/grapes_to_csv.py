import os
import json
import csv


def load_json(path):
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_rows(data):
    """Extract grape id and name."""
    rows = []

    varieties = data.get("varieties", [])

    for i, grape in enumerate(varieties):

        grape_name = grape[0] if grape else ''

        rows.append([
            i,
            grape_name
        ])

    return rows


def write_csv(path, rows):
    """Write rows to CSV file."""
    header = [
        "id",
        "grape_name"
    ]

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        writer.writerow(header)
        writer.writerows(rows)


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))

    json_path = os.path.join(script_dir, 'grape_names.json')
    csv_path = os.path.join(script_dir, 'grapes.csv')

    data = load_json(json_path)

    rows = extract_rows(data)

    write_csv(csv_path, rows)


if __name__ == "__main__":
    main()
