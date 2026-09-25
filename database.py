import psycopg

from config import DB_CONFIG


def get_connection():
    return psycopg.connect(**DB_CONFIG)


def add_user(vk_id, first_name, last_name):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                INSERT INTO users (vk_id, first_name, last_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (vk_id) DO NOTHING;
                """,
            (vk_id, first_name, last_name),
        )


def add_candidate(vk_id, first_name, last_name, profile_url):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                INSERT INTO candidates (
                    vk_id,
                    first_name,
                    last_name,
                    profile_url
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (vk_id) DO UPDATE
                SET first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    profile_url = EXCLUDED.profile_url
                RETURNING id;
                """,
            (vk_id, first_name, last_name, profile_url),
        )

        result = cursor.fetchone()
        return result[0]


def add_to_favorites(user_vk_id, candidate_id):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT id
                FROM users
                WHERE vk_id = %s;
                """,
            (user_vk_id,),
        )

        user = cursor.fetchone()

        if user is None:
            return False

        cursor.execute(
            """
                INSERT INTO favorites (user_id, candidate_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, candidate_id) DO NOTHING;
                """,
            (user[0], candidate_id),
        )

        return True


def get_favorites(user_vk_id):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    candidates.first_name,
                    candidates.last_name,
                    candidates.profile_url
                FROM favorites
                JOIN users
                    ON favorites.user_id = users.id
                JOIN candidates
                    ON favorites.candidate_id = candidates.id
                WHERE users.vk_id = %s
                ORDER BY favorites.id;
                """,
            (user_vk_id,),
        )

        return cursor.fetchall()


if __name__ == "__main__":
    connection = get_connection()
    print("Подключение к PostgreSQL успешно!")
    connection.close()
