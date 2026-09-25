import random

import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll

from config import VK_TOKEN
from database import (
    add_candidate,
    add_to_favorites,
    add_user,
    get_favorites,
)
from vk_api_client import (
    calculate_age,
    get_top_photos,
    get_user_info,
    get_vk_session,
    search_users,
)

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

search_vk = get_vk_session()

user_candidates = {}
current_candidates = {}
waiting_for_age = {}


def send_message(user_id, message, attachment=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.randint(1, 2_147_483_647),
        attachment=attachment,
    )


def show_candidate(user_id):
    candidates = user_candidates.get(user_id, [])

    if not candidates:
        send_message(
            user_id,
            "Анкеты закончились. Напиши «поиск», " "чтобы выполнить новый поиск.",
        )
        return

    candidate = candidates.pop(0)

    candidate_vk_id = candidate["id"]
    first_name = candidate["first_name"]
    last_name = candidate["last_name"]

    profile_url = f"https://vk.com/id{candidate_vk_id}"

    candidate_id = add_candidate(candidate_vk_id, first_name, last_name, profile_url)

    current_candidates[user_id] = candidate_id

    photos = get_top_photos(search_vk, candidate_vk_id)

    attachments = []

    for photo in photos:
        attachments.append(f"photo{photo['owner_id']}_{photo['id']}")

    attachment = ",".join(attachments)

    message = (
        f"{first_name} {last_name}\n"
        f"{profile_url}\n\n"
        "Напиши:\n"
        "«следующая» — следующая анкета\n"
        "«в избранное» — добавить в избранное"
    )

    send_message(user_id, message, attachment if attachment else None)


def perform_search(user_id, age, user):
    sex = user.get("sex")

    if sex not in (1, 2):
        send_message(user_id, "В профиле не указан пол.")
        return

    city = user.get("city")

    if not city:
        send_message(user_id, "В профиле не указан город.")
        return

    city_id = city["id"]

    candidates = search_users(search_vk, age, sex, city_id)

    if not candidates:
        send_message(user_id, "Подходящих открытых анкет не найдено.")
        return

    user_candidates[user_id] = candidates

    send_message(user_id, f"Нашёл подходящие анкеты: {len(candidates)}.")

    show_candidate(user_id)


def start_search(user_id):
    user = get_user_info(search_vk, user_id)

    if user is None:
        send_message(user_id, "Не удалось получить информацию о профиле.")
        return

    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")

    add_user(user_id, first_name, last_name)

    bdate = user.get("bdate")
    age = calculate_age(bdate)

    if age is None:
        waiting_for_age[user_id] = user

        send_message(
            user_id,
            "В профиле не указана полная дата рождения.\n"
            "Напиши свой возраст цифрами, например: 27",
        )
        return

    perform_search(user_id, age, user)


def show_favorites(user_id):
    favorites = get_favorites(user_id)

    if not favorites:
        send_message(user_id, "В избранном пока ничего нет.")
        return

    lines = ["Твоё избранное:\n"]

    for first_name, last_name, profile_url in favorites:
        lines.append(f"{first_name} {last_name}\n{profile_url}")

    send_message(user_id, "\n\n".join(lines))


def handle_message(user_id, text):
    text = text.lower().strip()

    if user_id in waiting_for_age:
        if not text.isdigit():
            send_message(user_id, "Возраст нужно написать цифрами. " "Например: 27")
            return

        age = int(text)

        if age < 18 or age > 100:
            send_message(user_id, "Укажи возраст от 18 до 100 лет.")
            return

        user = waiting_for_age.pop(user_id)

        perform_search(user_id, age, user)
        return

    if text in ("начать", "start", "привет"):
        send_message(
            user_id,
            "Привет! Я VKinder.\n\n"
            "Доступные команды:\n"
            "«поиск» — найти подходящую анкету\n"
            "«следующая» — показать следующую\n"
            "«в избранное» — сохранить анкету\n"
            "«избранное» — показать сохранённые анкеты",
        )

    elif text == "поиск":
        start_search(user_id)

    elif text == "следующая":
        show_candidate(user_id)

    elif text == "в избранное":
        candidate_id = current_candidates.get(user_id)

        if candidate_id is None:
            send_message(user_id, "Сначала выполни поиск анкеты.")
            return

        added = add_to_favorites(user_id, candidate_id)

        if added:
            send_message(user_id, "Анкета добавлена в избранное ❤️")
        else:
            send_message(user_id, "Не удалось добавить анкету.")

    elif text == "избранное":
        show_favorites(user_id)

    else:
        send_message(
            user_id,
            "Не знаю такой команды.\n" "Напиши «начать», чтобы посмотреть команды.",
        )


def main():
    print("VKinder запущен!")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            handle_message(event.user_id, event.text)


if __name__ == "__main__":
    main()
