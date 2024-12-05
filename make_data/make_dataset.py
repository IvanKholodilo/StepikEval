import json

x = []
with open('parsed_targets.json') as f:
    data = json.load(f)
count = 0
dataset = []
import pandas as pd


def get_rev():
    words = []
    with open('data/word_list.json', 'r') as cat_file:
        catalog = json.load(cat_file)
        for x in catalog:
            a = x.encode().decode('utf-8')
            words.append(a)
    return words


for text, target in data.items():
    try:
        ans = target['response']['alternatives'][0]['message']['text'].replace(",", "").replace(" ", "").replace("\n",
                                                                                                                 "").replace(
            '\\', "")
        txt = text.encode().decode('utf-8')
        txt = txt.split("Отзыв для разметки:")[1].split("Ответ должен содержать")[0].replace("\n", "")[5:-5]
        dataset.append([txt, ans])
    except Exception as e:
        print(str(count) + " " + str(e))
    count += 1

df = pd.DataFrame(dataset, columns=['text', 'target'])
print(df)
df.to_csv('data/data.csv', index=False, encoding='utf-8')
# df2 = pd.read_csv('output2.csv')
# df1 = pd.read_csv('output.csv')
# result = pd.concat([df1, df2], ignore_index=True)
# result.to_csv('output_2.csv', index=False, encoding='utf-8', sep = "$")
#
# print(result)
