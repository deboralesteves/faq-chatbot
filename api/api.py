from flask import Flask
from atlassian import Confluence
import os
CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
USER_EMAIL = os.getenv('USER_EMAIL')
USER_TOKEN = os.getenv('USER_TOKEN')

import re
import random
import string
import json
import nltk
from langdetect import detect
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings
warnings.filterwarnings('ignore')

noSimilarityResponse = 'I apologize, I did not understand :( Please try to rephrase your message.'

#Download the punkt package
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Confluence connection
try: 
        confluenceUrl = CONFLUENCE_URL
        email = USER_EMAIL
        apiToken = USER_TOKEN

        confluence = Confluence(
        url=confluenceUrl,
        username=email,
        password=apiToken,
        cloud=True)
        
except Exception as e:
        print (e)

#Clean up user input
def tokenize_user_message(user_input):

        words_list = user_input.lower().split()
        # remove non alphabetic values
        words_list = [word for word in words_list if word.isalpha()]

        if detect(user_input) is 'de':
                stop_words = set(nltk.corpus.stopwords.words('german'))
        else:
                stop_words = set(nltk.corpus.stopwords.words('english'))

        words_list = [w for w in words_list if not w in stop_words]
        words = ' '.join(words_list)

        return words

#Get the intents
with open("intents.json") as file:
        data = json.load(file)

#A function to return a random greeting response to a users greeting
def greeting_response(user_input):
        text_list = user_input.lower().split()

        #Bots greeting response
        bot_greetings = ['howdy', 'hi', 'hey', 'hello', 'ola']

        #Users greeting
        user_greetings = ['mekie', 'hey', 'hello', 'hi', 'greetings']

        for word in text_list:
                if word in user_greetings:
                        return random.choice(bot_greetings)

# query confluence

def query_confluence(user_input):

        try: 
                cql= 'text ~ "' + user_input + '" and type = page'
                # html removal
                regex = re.compile('<.*?>')
                articles_list = []

                response = confluence.cql(cql, start=0, limit=None, expand=None, include_archived_spaces=None, excerpt=None)

                for result in response["results"]:
                        pageUrl = confluenceUrl + 'wiki' + result["url"]
                        pageId = result['content']['id']

                        page = confluence.get_page_by_id(pageId, expand="body.storage", status=None, version=None)
                        pageContent = page['body']['storage']['value']
                        cleanPageContent = re.sub(regex, '', pageContent)
                        articles_list.append(cleanPageContent)

                return articles_list
        
        except Exception as e:
                print (e)

#Sorts the indexes to go from highest to lowest similarity score
def index_sort(list_var):
        length = len(list_var)
        list_index = list(range(0, length))

        x = list_var

        for i in range(length):
                for j in range(length):
                        if x[list_index[i]] > x[list_index[j]]:
                                #Swap
                                temp_var = list_index[i]
                                list_index[i] = list_index[j]
                                list_index[i] = temp_var
        return list_index

#Query the bot
def ask_the_bot(user_input):
        
        confluenceResponse = query_confluence(user_input)
 
        confluenceResponse.append(user_input)
        bot_response = ''
        countMatrix = CountVectorizer().fit_transform(confluenceResponse)
        similarity_scores = cosine_similarity(countMatrix[-1], countMatrix)
        similarity_scores_list = similarity_scores.flatten()
        index = index_sort(similarity_scores_list)
        index= index[1:]
        response_flag = 0

        j = 0
        for i in range(len(index)):
                if similarity_scores_list[index[i]] > 0.0:
                        bot_response = bot_response+''+confluenceResponse[index[i]]
                        response_flag = 1
                        j = j+1
                        if j > 2:
                                break
        
        if response_flag == 0:
                bot_response = bot_response+' '+ noSimilarityResponse

        return bot_response

# API
app = Flask(__name__)

@app.route('/send-message/<userMessage>', methods = ['POST'])
def chat(userMessage):

        robot_greeting = greeting_response(userMessage)

        if robot_greeting:
                response = robot_greeting
        else:
                tokenized_user_message = tokenize_user_message(userMessage)

                if tokenized_user_message:
                        response = ask_the_bot(tokenized_user_message)
                else:
                        response = noSimilarityResponse

 
        return { "messages": [response] }
