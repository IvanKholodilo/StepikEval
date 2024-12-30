import time
from time import sleep

import torch
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from translators import translate_text


class Review:
    def __init__(self):
        self.scores = []
        self.emotions = []
        self.stars = None


class Course:
    def __init__(self, classifier):
        self.reviews = []
        self.classifier = classifier

        self.average_stars = None

        self.total_score = None
        self.detail_score = None
        self.deep_score = None
        self.material_quality_score = None
        self.problems_quality_score = None
        self.coach_skills_score = None
        self.practice_experience_score = None
        self.feedback_score = None

        self.positive = None
        self.negative = None
        self.positive_part = None
        self.negative_part = None
        self.important_positive_part = None
        self.important_negative_part = None

        self.important_rews_amount = None
        self.important_rews_part = None

    def get_info(self, url: str):
        self.reviews.clear()
        self.average_stars = 0

        self.total_score = 0
        self.detail_score = 0
        self.deep_score = 0
        self.material_quality_score = 0
        self.problems_quality_score = 0
        self.coach_skills_score = 0
        self.practice_experience_score = 0
        self.feedback_score = 0

        self.positive = 0
        self.negative = 0
        self.positive_part = 0
        self.negative_part = 0
        self.important_positive_part = 0
        self.important_negative_part = 0

        self.important_rews_amount = 0
        self.important_rews_part = 0

        options = Options()
        options.add_argument("--headless")
        browser = webdriver.Firefox(options=options)
        browser.get(url)
        sleep(3)
        print('Сбор данных...')
        try:
            button = browser.find_elements(By.CSS_SELECTOR,
                                       "button:not(.st-button_style_none).btn-details")[-1]
            while button.text == 'Показать ещё':
                    try:
                        sleep(0.02)
                        button = browser.find_elements(By.CSS_SELECTOR,
                                                    "button:not(.st-button_style_none).btn-details")[-1]
                        if button.text == 'Показать ещё':
                            button.click()
                        else:
                            break

                    except Exception as exp:
                        print(exp)
                        break
            
        except Exception as exp:
            print(exp)

        html = browser.page_source
        browser.close()

        bs = BeautifulSoup(html, 'html.parser')
        rews = bs.find_all('div', {'class': 'show-more__content'})
        global_exeption = None
        
        vect_7_ids = []
        vect_7_masks = []
        vect_emotions_ids = []
        vect_emotions_masks = []
        x = time.time()
        text = []
        for rev in rews:
            try:
                text.append(rev.contents[0])
                self.reviews.append(Review())
            except Exception as exp:
                print(exp)
                global_exeption = exp
                continue
            
        if len(text) > 0:
            vect_7_ids, vect_7_masks = self.classifier.get_ids_and_mask(text)
            vect_emotions_ids, vect_emotions_masks = self.classifier.get_ids_and_mask(text)
            
            output_data_for7 = self.classifier.predict_stack(vect_7_ids, vect_7_masks)
            output_data_for_emotions = self.classifier.predict_stack_emotions(vect_emotions_ids, vect_emotions_masks)
            
            for scores, emotions, review in zip(output_data_for7, output_data_for_emotions, self.reviews):
                review.scores = scores
                review.emotions = emotions
                if scores[0] >= 0.5:
                    self.important_rews_amount = self.important_rews_amount + 1
                self.detail_score = self.detail_score + scores[0]
                self.deep_score = self.deep_score + scores[1]
                self.material_quality_score = self.material_quality_score + scores[2]
                self.problems_quality_score = self.problems_quality_score + scores[3]
                self.coach_skills_score = self.coach_skills_score + scores[4]
                self.practice_experience_score = self.practice_experience_score + scores[5]
                self.feedback_score = self.feedback_score + scores[6]
                self.negative = self.negative + emotions[0]
                self.positive = self.positive + emotions[1]
                if emotions[0] > emotions[1]:
                    self.negative_part = self.negative_part + 1
                    if scores[0] >= 0.5:
                        self.important_negative_part = self.important_negative_part + 1
                else:
                    self.positive_part = self.positive_part + 1
                    if scores[0] >= 0.5:
                        self.important_positive_part = self.important_positive_part + 1

            try:
                lenth = len(self.reviews)
                self.detail_score = self.detail_score / lenth
                self.deep_score = self.deep_score / lenth
                self.material_quality_score = self.material_quality_score / lenth
                self.problems_quality_score = self.problems_quality_score / lenth
                self.coach_skills_score = self.coach_skills_score / lenth
                self.practice_experience_score = self.practice_experience_score / lenth
                self.feedback_score = self.feedback_score / lenth

                self.negative = self.negative / lenth
                self.positive = self.positive / lenth
                self.negative_part = self.negative_part / lenth
                self.positive_part = self.positive_part / lenth
                self.important_positive_part = self.important_positive_part / self.important_rews_amount
                self.important_negative_part = self.important_negative_part / self.important_rews_amount

                self.important_rews_part = self.important_rews_amount / lenth

                stars_parsed = []
                summ = 0
                i = 0
                sections = bs.find_all('section', {'class': 'course-promo__main'})
                for section in sections:
                    for div in section.find_all('div', {'class': 'course-review-card course-promo-reviews__item'}):
                        for sp in div.find_all('span'):
                            for span in sp.find_all('span'):
                                try:
                                    span_cl = span['class'][1]
                                    if 'colored-star' in span_cl:
                                        summ = summ + 1
                                        i = i + 1
                                    elif 'uncolored-star' in span_cl:
                                        i = i + 1
                                    if i == 5:
                                        stars_parsed.append(summ)
                                        summ = 0
                                        i = 0
                                except Exception as exp:
                                    print('У span нет класса', exp)

                self.average_stars = sum(stars_parsed) / len(stars_parsed)

                tech = 0
                for rew, star in zip(self.reviews, stars_parsed):
                    rew.stars = star
                    for i in range(1, 7):
                        tech = rew.scores[i] + tech
                    self.total_score = self.total_score + tech * (rew.emotions[1] - rew.emotions[0]) * rew.scores[0]
                    tech = 0

                self.total_score = 100 * ((((self.total_score / (self.detail_score * lenth)) / 6) + 1) / 2)
                print(f"Время оценки: {time.time()-x}")
                return self.total_score
            except Exception as exp:
                print('Ошибка.', exp)
                return global_exeption
        else:
            raise Exception('Course has no reviews')


class CourseClassifier:
    def __init__(self):
        model_name = "cointegrated/rubert-tiny2"
        num_labels = 7
        device = 'cpu'
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
        self.model.load_state_dict(
            torch.load('models/categories.pth', weights_only=False, map_location=torch.device(device)))
        self.model.eval()
        self.binary_model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
        self.binary_model.load_state_dict(
            torch.load('models/binary.pth', weights_only=False, map_location=torch.device(device)))
        self.binary_model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def predict_stack(self, ids, mask):
        with torch.no_grad():
            output = self.model(ids, mask)

        if isinstance(output, tuple):
            output = output[0]

        return torch.sigmoid(output.logits).tolist()
    
    def predict_stack_emotions(self, ids, mask):
        with torch.no_grad():
            output = self.binary_model(ids, mask)

        if isinstance(output, tuple):
            output = output[0]

        return torch.sigmoid(output.logits).tolist()
    
    def get_ids_and_mask(self, text: str):
        encodings = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors='pt'
        )        
        input_ids = encodings["input_ids"].clone().detach()
        attention_mask = encodings['attention_mask']
        
        return input_ids, attention_mask
        
    def predict_scores(self, text: str):
        encodings = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors='pt'
        )
        input_ids = encodings["input_ids"].clone().detach()
        attention_mask = encodings['attention_mask']
        output = None
        with torch.no_grad():
            output = self.model(input_ids, attention_mask)

        if isinstance(output, tuple):
            output = output[0]

        return torch.sigmoid(output.logits).tolist()

    def predict_emotions(self, text: str):
        text = translate_text(text, to_language='en')
        encodings = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors='pt'
        )
        input_ids = encodings["input_ids"].clone().detach()
        attention_mask = encodings['attention_mask']
        output = None
        with torch.no_grad():
            output = self.binary_model(input_ids, attention_mask)

        if isinstance(output, tuple):
            output = output[0]

        return torch.sigmoid(output.logits).tolist()
