from config.settings import Settings


def main():
    settings = Settings()
    print(f"FinReview starting... (database: {settings.database_path})")


if __name__ == "__main__":
    main()
