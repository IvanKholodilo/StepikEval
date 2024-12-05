import torch
from transformers import AutoTokenizer, AutoModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from time import sleep
from bs4 import BeautifulSoup
from translators import translate_text

class Review():
    def __init__(self):
        self.scores = []
        self.emotions = []
        self.stars = []
    
    
    
class Course():
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
        
    def get_info(self, url: str):
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
        options = Options()
        options.add_argument("--headless")
        browser = webdriver.Firefox(options=options)
        browser.get(url)
        sleep(3)
        button = browser.find_elements(By.CSS_SELECTOR, 
                                      "button:not(.st-button_style_none).btn-details")[-1]
        try:
            while button.text == 'Показать ещё':
                try:
                    sleep(0.1)
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
        for rev in rews:
            try:
                review = Review()
                scores = self.classifier.predict_scores(rev.contents[0])[0]
                emotions = self.classifier.predict_emotions(rev.contents[0])[0]
                review.scores = scores
                review.emotions = emotions
                self.detail_score = self.detail_score + scores[0]
                self.deep_score = self.deep_score + scores[1]
                self.material_quality_score = self.material_quality_score + scores[2]
                self.problems_quality_score = self.problems_quality_score + scores[3]
                self.coach_skills_score = self.coach_skills_score + scores[4]
                self.practice_experience_score = self.practice_experience_score + scores[5]
                self.feedback_score = self.feedback_score + scores[6]
                self.negative = self.negative + emotions[0]
                self.positive = self.positive + emotions[1]
                self.reviews.append(review)
            except Exception as exp:
                continue
            
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
        self.average_stars = float(bs.find_all('span', {'class': 'course-promo-summary__average'})[0].contents[0])
        
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
                
        tech = 0
        for rew, star in zip(self.reviews, stars_parsed):
            rew.stars = star
            for i in range(1, 7):
                tech = rew.scores[i] * (rew.emotions[1] - rew.emotions[0]) * rew.scores[0] + tech
            self.total_score = self.total_score + tech
            tech = 0
                
                
    
class CourseClassifier():
    def __init__(self):
        bert_model = AutoModel.from_pretrained('cointegrated/rubert-tiny2')
        self.model = TextClassifier(bert_model)
        self.model.load_state_dict(torch.load('models/categories.pth', weights_only=False, map_location=torch.device('cpu')))
        self.model.eval()
        self.binary_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2) 
        self.binary_model.load_state_dict(torch.load('models/binary.pth', weights_only=False, map_location=torch.device('cpu')))
        self.binary_model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained('cointegrated/rubert-tiny2')
        self.eng_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    def predict_scores(self, text: str):
        encodings = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512, 
            return_tensors='pt'
        )
        input_ids = torch.tensor(encodings["input_ids"])
        attention_mask = encodings['attention_mask']
        output = None
        with torch.no_grad():
            output = self.model(input_ids, attention_mask)

        if isinstance(output, tuple):
            output = output[0]
            
        return torch.sigmoid(output).tolist()
    
    def predict_emotions(self, text: str):
        text = translate_text(text, to_language = 'en')
        encodings = self.eng_tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512, 
            return_tensors='pt'
        )
        input_ids = torch.tensor(encodings["input_ids"])
        attention_mask = encodings['attention_mask']
        output = None
        with torch.no_grad():
            output = self.binary_model(input_ids, attention_mask)

        if isinstance(output, tuple):
            output = output[0]
            
        return torch.sigmoid(output.logits).tolist()


class TextClassifier(torch.nn.Module):
    def __init__(self, bert_model):
        super(TextClassifier, self).__init__()
        self.bert = bert_model
        self.dropout = torch.nn.Dropout(0.2)
        self.pooler = torch.nn.Sequential(
            torch.nn.Linear(bert_model.config.hidden_size, bert_model.config.hidden_size),
            torch.nn.Tanh(),
        )
        self.classifier = torch.nn.Linear(bert_model.config.hidden_size, 7)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state
        mean_pooling = torch.mean(hidden_states, dim=1)
        pooled_output = self.pooler(mean_pooling)
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits
    
    
    
Course(CourseClassifier()).get_info('https://stepik.org/course/56237')