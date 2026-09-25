import os
from datetime import datetime, timezone

import vk_api
from dotenv import load_dotenv

load_dotenv()

USER_TOKEN = os.getenv("USER_TOKEN")


def get_vk_session():
    vk_session = vk_api.VkApi(token=USER_TOKEN)
    return vk_session.get_api()


def get_user_info(vk, user_id):
    users = vk.users.get(
        user_ids=user_id,
        fields="sex,bdate,city",
    )

    if not users:
        return None

    return users[0]


def calculate_age(bdate):
    if not bdate:
        return None

    parts = bdate.split(".")

    if len(parts) != 3:
        return None

    birth_date = datetime.strptime(
        bdate,
        "%d.%m.%Y",
    ).replace(tzinfo=timezone.utc)

    today = datetime.now(timezone.utc)

    age = today.year - birth_date.year

    if (today.month, today.day) < (
        birth_date.month,
        birth_date.day,
    ):
        age -= 1

    return age


def search_users(vk, age, sex, city_id, count=20):
    # Ищем противоположный пол
    search_sex = 1 if sex == 2 else 2

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

    for user in result["items"]:
        if not user.get("is_closed", True):
            users.append(user)

    return users


def get_top_photos(vk, user_id):
    try:
        photos = vk.photos.get(
            owner_id=user_id,
            album_id="profile",
            extended=1,
            count=100,
        )
    except vk_api.exceptions.ApiError:
        return []

    photos_list = photos["items"]

    photos_list.sort(
        key=lambda photo: photo["likes"]["count"],
        reverse=True,
    )

    return photos_list[:3]


if __name__ == "__main__":
    vk = get_vk_session()
    print("Подключение к VK API успешно!")
