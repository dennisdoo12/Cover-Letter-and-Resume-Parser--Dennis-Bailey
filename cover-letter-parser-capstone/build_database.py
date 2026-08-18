import csv
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "onet_data"
DB_PATH = BASE_DIR / "onet.db"


def find_csv(keyword):
    """
    Find an O*NET CSV file even if its exact filename
    differs slightly between database versions.
    """
    keyword = keyword.lower()

    for path in DATA_DIR.glob("*.csv"):
        if keyword in path.stem.lower():
            return path

    raise FileNotFoundError(
        f"Could not find a CSV containing '{keyword}' "
        f"in {DATA_DIR}"
    )


def create_table_from_csv(connection, table_name, csv_path):
    print(f"Importing {csv_path.name} -> {table_name}")

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.reader(file)

        headers = next(reader)

        # SQLite-safe column names
        columns = []

        for header in headers:
            clean = (
                header.strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
                .replace("/", "_")
                .replace(".", "_")
            )

            columns.append(clean)

        connection.execute(
            f"DROP TABLE IF EXISTS {table_name}"
        )

        column_sql = ", ".join(
            f'"{column}" TEXT'
            for column in columns
        )

        connection.execute(
            f"""
            CREATE TABLE {table_name} (
                {column_sql}
            )
            """
        )

        placeholders = ", ".join(
            "?"
            for _ in columns
        )

        quoted_columns = ", ".join(
            f'"{column}"'
            for column in columns
        )

        insert_sql = f"""
            INSERT INTO {table_name}
            ({quoted_columns})
            VALUES ({placeholders})
        """

        count = 0

        for row in reader:

            # Ignore malformed rows rather than crashing.
            if len(row) != len(columns):
                continue

            connection.execute(
                insert_sql,
                row
            )

            count += 1

        print(
            f"  Added {count:,} rows."
        )


def main():

    print()
    print("Building ResumeRank O*NET database...")
    print()

    connection = sqlite3.connect(DB_PATH)

    try:

        # These are the O*NET datasets most useful
        # to ResumeRank.

        datasets = {
            "occupations": "occupation_data",
            "job_titles": "job_titles",
            "software_skills": "software_skills",
            "essential_skills": "essential_skills",
            "emerging_tasks": "emerging_tasks",
            "education": "education"
        }

        for table_name, filename_keyword in datasets.items():

            try:

                csv_path = find_csv(
                    filename_keyword
                )

                create_table_from_csv(
                    connection,
                    table_name,
                    csv_path
                )

            except FileNotFoundError as error:

                print(
                    f"Skipping {table_name}: {error}"
                )

        connection.commit()

    finally:

        connection.close()

    print()
    print("Database created successfully!")
    print(f"Location: {DB_PATH}")
    print()


if __name__ == "__main__":
    main()