from src.load_into_datalake import main as load_into_datalake
from src.clickhouse import initialize_warehouse


def main():
    initialize_warehouse()
    load_into_datalake()


if __name__ == "__main__":
    main()
