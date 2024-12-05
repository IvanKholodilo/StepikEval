import asyncio
import json
import time
import aiohttp
from config import *


def get_promt(rev):
    return f'''
    Оцени курс по отзыву, выставив оценки по 7 признакам упоминания, если оно есть - 1, если нет - 0.

    Признаки:
    1. Подробность отзыва
    2. Глубина курса
    3. Качество обучающих материалов
    4. Качество задач
    5. Умения преподавателя
    6. Практическая направленность
    7. Качество обратной связи

    Пример отзыва:
    "Круто. Мне понравилось"

    Ожидаемый вывод: 0, 0, 0, 0, 0, 0, 0

    Отзыв для разметки:
    "{rev}"

    Ответ должен содержать только бинарные цифры (0 или 1). Проверьте точность перед отправкой.
    '''


class YandexGPT:
    def __init__(self, folder_id: str, auth: str):
        self.auth = auth
        self.folder_id = folder_id
        self.completion_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completionAsync"

    async def send_async_request(self, message: str, temperature: float = 0.2, max_tokens: int = 1000):
        headers = {
            "Authorization": f"Bearer {self.auth}",
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": [{"role": "user", "text": message}]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.completion_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
        except aiohttp.ClientError as e:
            print(f"Network error occurred: {e}")
            return {}
        except Exception as e:
            print(f"An error occurred: {e}")
            return {}


async def check_status(task_id, auth):
    status_url = f"https://llm.api.cloud.yandex.net/operations/{task_id}"
    headers = {
        "Authorization": f"Bearer {auth}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(status_url, headers=headers) as response:
                # Проверяем статус ответа
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Ошибка: получен статус {response.status} для task_id {task_id}")
                    print(response)
                    time.sleep(10)
                    return {}
    except aiohttp.ClientError as e:
        print(f"Ошибка сети при запросе к {status_url}: {e}")
        print(e.__doc__)
        time.sleep(10)
        return {}
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        print(e.__doc__)

        time.sleep(10)
        return {}


def get_rev():
    words = []
    with open('data/word_list.json', 'r') as cat_file:
        catalog = json.load(cat_file)
        for x in catalog:
            a = x.encode().decode('utf-8')
            words.append(a)
    print(words[:2])
    return words


async def main():
    gpt_client = YandexGPT(folder_id, auth_token)

    from tqdm import tqdm

    data = {}

    for rev in tqdm(get_rev()):
        text = get_promt(rev)
        result = await gpt_client.send_async_request(text)
        data.update({text: result})
    with open('data/промежуточные.json', 'w') as dataset:
        json.dump(data, dataset, indent=4)
    results = {}
    # with open('our_dataset.json') as f:
    #     data = json.load(f)
    for text, task in tqdm(data.items()):
        id_t = task['id']
        result = await check_status(id_t, auth_token)
        results.update({text: result})

    with open('data/parsed_targets.json', 'w') as dataset:
        json.dump(results, dataset, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
