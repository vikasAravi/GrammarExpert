import requests
from .error import Error
import re
import nltk
from nltk.corpus import stopwords
languagecheckurl = 'http://localhost:8082/v2/check'
class Report:
    stop_words = set(stopwords.words('english'))

    def __init__(self, essay, word_limit):
        global languagecheckurl

        self.essay = re.sub(' +',' ',essay)

        # replace all continuous spaces with single space

        payload = {"text":self.essay,"language":"en-US", "enabledOnly":"false"}
        response = requests.post(languagecheckurl,data = payload)
        self.errors = [Error(m) for m in response.json()['matches']]
        self.words = re.sub(r"[.,?!;():\"\']", " ", self.essay).split()
        self.wordCount = len(self.words)
        self.score = 10

        #word limit penalty
        x = word_limit - self.wordCount
        self.wordlimitpenalty = 0
        if(self.wordCount <= word_limit//2):
            self.wordlimitpenalty = 10
        elif x > 0:
            self.wordlimitpenalty = 3*2*(x)/word_limit
        
        #average_words_per_sentences
        sentencesList = self.essay.split('.')
        self.avg_words_per_sentences = self.wordCount / len(sentencesList)

        #words_without_stop_words
        words_without_stop_words = [word for word in self.words if word not in Report.stop_words]
        
        #avergage_word_length_without_stopwords
        self.avg_word_length_without_stopwords = sum(map(len, words_without_stop_words))/len(words_without_stop_words)
 
        desired_words_per_sentence = 20
        min_words_per_sentence = 10
        self.sentencequalitypenalty=0
        #penality regarding avg_words_per_sentences
        if self.avg_words_per_sentences < min_words_per_sentence:
            self.sentencequalitypenalty = 2
        elif self.avg_words_per_sentences <=desired_words_per_sentence:
            self.sentencequalitypenalty = ((desired_words_per_sentence-self.avg_words_per_sentences)/desired_words_per_sentence)*4

        desired_word_length = 8
        min_avg_word_len = 4
        self.wordqualitypenalty = 0
        if self.avg_word_length_without_stopwords < min_avg_word_len:
            self.wordqualitypenalty = 2
        #penality regarding avg_word_length without_stop_words
        elif self.avg_word_length_without_stopwords<desired_word_length:
            self.wordqualitypenalty = ((desired_word_length-self.avg_word_length_without_stopwords)/desired_word_length)*4

        
        #spellingmistakes and grammar mistakes
        self.spellingErrorCount = len(list(filter(lambda x:x.errorType()=='spelling', self.errors)))
        self.grammarErrorCount = len(self.errors)-self.spellingErrorCount
        #add properties for average worldlenght, sentence length, readability index etc.
        self.score -= ((self.spellingErrorCount * 0.25) + (self.grammarErrorCount * 0.25)) + self.sentencequalitypenalty + self.wordqualitypenalty + self.wordlimitpenalty
        if self.score < 0:
            self.score = 0
        
        # round'em up to 2 decimal places
        self.score = round(self.score,2)
        self.wordlimitpenalty = round(self.wordlimitpenalty, 2)
        self.wordqualitypenalty = round(self.wordqualitypenalty, 2)
        self.sentencequalitypenalty = round(self.sentencequalitypenalty, 2)

    def reprJSON(self):
        return dict(answer=self.essay, score = self.score,errors = [e.reprJSON() for e in self.errors],
        wordCount = self.wordCount, spellingErrorCount = self.spellingErrorCount, wordlimitpenalty=self.wordlimitpenalty,
        sentencequalitypenalty = self.sentencequalitypenalty, wordqualitypenalty = self.wordqualitypenalty,
        grammarErrorCount = self.grammarErrorCount)