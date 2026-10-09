from datetime import datetime, timezone

import vk_api
from vk_api.exceptions import ApiError

from config import USER_TOKEN


def get_vk_session():
    if not USER_TOKEN:
        raise ValueError("USER_TOKEN не найден в файле .env")

    vk_session = vk_api.VkApi(token=USER_TOKEN)
    return vk_session.get_api()


def get_user_info(vk, user_id):
    try:
        users = vk.users.get(
            user_ids=user_id,
            fields="sex,bdate,city",
        )

        if not users:
            return None

        return users[0]

    except (ApiError, KeyError, TypeError) as error:
        print(f"Ошибка получения пользователя: {error}")
        return None


def calculate_age(bdate):
    if not bdate:
        return None

    try:
        birth_date = (
            datetime.strptime(
                bdate,
                "%d.%m.%Y",
            )
            .replace(tzinfo=timezone.utc)
            .date()
        )

    except (ValueError, TypeError):
        return None

    today = datetime.now(timezone.utc).date()

    age = today.year - birth_date.year

    if (today.month, today.day) < (
        birth_date.month,
        birth_date.day,
    ):
        age -= 1

    if age < 18 or age > 100:
        return None

    return age


def search_users(vk, age, sex, city_id, count=20):
    search_sex = 1 if sex == 2 else 2

    try:
        result = vk.users.search(
            age_from=age,
            age_to=age,
            sex=search_sex,
            city=city_id,
            status=6,
            has_photo=1,
            count=count,
            fields="city,bdate,sex",
        )

        users = []

        for user in result.get("items", []):
            if not user.get("is_closed", True):
                users.append(user)

        return users

    except (ApiError, KeyError, TypeError) as error:
        print(f"Ошибка поиска пользователей: {error}")
        return []


def get_top_photos(vk, user_id):
    try:
        photos = vk.photos.get(
            owner_id=user_id,
            album_id="profile",
            extended=1,
            count=100,
        )

        photos_list = photos.get("items", [])

        photos_list.sort(
            key=lambda photo: (photo.get("likes") or {}).get("count", 0),
            reverse=True,
        )

        return photos_list[:3]

    except (ApiError, KeyError, TypeError) as error:
        print(f"Ошибка получения фотографий: {error}")
        return []


if __name__ == "__main__":
    try:
        vk = get_vk_session()
        user = vk.users.get()

        print("Подключение к VK API успешно!")

        if user:
            print(
                "Пользователь:",
                user[0].get("first_name", ""),
            )

    except ApiError as error:
        print(f"Ошибка авторизации VK: {error}")
