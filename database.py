import psycopg2

from config import DB_CONFIG


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def add_user(vk_id, first_name, last_name):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (vk_id, first_name, last_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (vk_id) DO NOTHING;
                """,
                (vk_id, first_name, last_name),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_candidate(vk_id, first_name, last_name, profile_url):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
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
            candidate_id = result[0]

        connection.commit()
        return candidate_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_to_favorites(user_vk_id, candidate_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
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

        connection.commit()
        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_favorites(user_vk_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
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

            favorites = cursor.fetchall()

        return favorites

    finally:
        connection.close()


if __name__ == "__main__":
    connection = get_connection()
    print("Подключение к PostgreSQL успешно!")
    connection.close()
