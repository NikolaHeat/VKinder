from database import get_connection


def create_tables():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    vk_id BIGINT UNIQUE NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id SERIAL PRIMARY KEY,
                    vk_id BIGINT UNIQUE NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    profile_url TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    candidate_id INTEGER NOT NULL
                        REFERENCES candidates(id) ON DELETE CASCADE,
                    UNIQUE (user_id, candidate_id)
                );
            """)

        connection.commit()
        print("Таблицы успешно созданы!")

    finally:
        connection.close()


if __name__ == "__main__":
    create_tables()
