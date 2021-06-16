# -*- coding: utf-8 -*-
"""Chatbot Recommender Laptop with LSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dqk3m1uNg6E4RQ0K6WjWLUT15Tgg03Iq

#Natural Language Processing Chatbot Recommender Laptop with LSTM

## Steven Tjayadi / 535180085

###1. Import Library NLTK
"""
import nltk
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

# Download ini di google colab / Jupyter notebook untuk package tambahan
nltk.download('punkt')
nltk.download('wordnet')

"""### 2. Import Library tambahan untuk menyimpan file seperti pandas , numpy , json dll"""

import json
import pickle
import random
import numpy as np
import pandas as pd

"""### 3. Import Library Machine Learning dan Deep Learning 
* Sklearn ( Machine Learning )
* Keras ( Deep Learning )
* tensorflow ( model deployment + integrated keras )
"""

import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from keras import preprocessing
from keras_preprocessing import image
from keras import Sequential
from keras.models import load_model
from keras.layers import Dense, Activation, Dropout , LSTM , Embedding
from keras.optimizers import SGD
from keras.preprocessing.text import Tokenizer

"""### 4. Melakukan import library Dataset Laptop 2 dan Dataset Chatbot"""

data_file = open('Dataset Chatbot Laptop.json').read()
intents = json.loads(data_file)
spek = pd.read_csv("Dataset Laptop 2.csv")

"""### 5. Membuat list baru untuk menyimpan data kata , kelas dan dokumen"""

words=[]
classes = []
documents = []
ignore_words = ['?', '!']

"""### 6. Melakukan looping dari json untuk melakukan preprocessing text"""

for intent in intents['intents']:
    for pattern in intent['patterns']:

        #tokenize each word
        w = nltk.word_tokenize(pattern)
        words.extend(w)
        #add documents in the corpus
        documents.append((w, intent['tag']))

        # add to our classes list
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

# lemmaztize and lower each word and remove duplicates
words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))
# sort classes
classes = sorted(list(set(classes)))

pickle.dump(words,open('testing_kata.pkl','wb'))
pickle.dump(classes,open('testing.pkl','wb'))

"""### 7. Melakukan training dan membuat bag of words"""

training = []
# create an empty array for our output
output_empty = [0] * len(classes)
# training set, bag of words for each sentence
for doc in documents:
    # initialize our bag of words
    bag = []
    # list of tokenized words for the pattern
    pattern_words = doc[0]
    # lemmatize each word - create base word, in attempt to represent related words
    pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_words]
    # create our bag of words array with 1, if word match found in current pattern
    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)
    
    # output is a '0' for each tag and '1' for current tag (for each pattern)
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1
    
    training.append([bag, output_row])

"""### 8. Melakukan pemisahkan antara training X dan Y """

# shuffle our features and turn into np.array
random.shuffle(training)
training = np.array(training)
# create train and test lists. X - patterns, Y - intents
train_x = list(training[:,0])
train_y = list(training[:,1])

train_x_convert = np.array(train_x)
train_y_convert = np.array(train_y)

print("Training data created")

"""### 9. Melakukan training data dengan Deep Learning"""

model = Sequential()
model.add(Dense(128 , input_shape=(len(train_x[0]),) , activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y_convert[0]), activation='softmax'))

# Compile model. Stochastic gradient descent with Nesterov accelerated gradient gives good results for this model
sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

#fitting and saving the model 
hist = model.fit(train_x_convert , train_y_convert , epochs=100, batch_size=5, verbose=1)
model.save('chatbot_model.h5', hist)

print("model created")

"""### 10. Melakukan load model untuk di testing dari hasil traning"""

model = load_model('chatbot_model.h5')
intents = json.loads(open('Dataset Chatbot Laptop.json').read())
words = pickle.load(open('testing_kata.pkl','rb'))
classes = pickle.load(open('testing.pkl','rb'))

"""### 11. Membuat Function Predict untuk melakukan predict pada Chatbot

#### 1. Melakukan Cleaning kalimat
"""

def clean_up_sentence(sentence):
    # tokenize the pattern - split words into array
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word - create short form for word
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

"""#### 2. Melakukan Bag of words untuk predict"""

def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)  
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s: 
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(np.array(bag))

"""#### 3. Melakukan Predict sesuai kelas kategori ( Classes )"""

def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words,show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

"""#### 4. Memanggil Response dalam Chatbot """

def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if(i['tag']== tag):
            result = random.choice(i['responses'])
            break
    return result

def chatbot_response(msg):
    ints = predict_class(msg, model)
    res = getResponse(ints, intents)
    return res

"""### 12. Melakukan Deployment ke website menggunakan Flask

#### 1. Melakukan instalasi flask-ngrok ( Jika di google colab )
"""



"""#### 2. Deployment hasil model melalui website dari Google Colab"""

from flask import Flask , render_template , request , url_for

app = Flask(__name__)

@app.route("/")
def home(): 
    return render_template("Design Chatbot.html")

list_question = []
list_answer = []

@app.route("/chatop")
def get_bot_response():    
    userText = request.args.get('msg')
    list_question.append(userText)
    list_answer.append(str(chatbot_response(userText)))     
    return str(chatbot_response(userText))
 
  
if __name__ == "__main__":
    app.run()

list_question

list_answer

"""### 13. Training Rekomendasi Laptop berdasarkan hasil input dan output Chatbot"""

dropped_column = ["Nama Laptop" , "Size" , "Processor" , "GPU" , "Storage" , "Link" , "Harga" , "RAM"] ## List column ambil dari responses chatbot nya
X = spek.drop(dropped_column , axis = 1)
value_x = X.values
Y = spek.iloc[:,0]
X

## Reshaping untuk Tokenizer text
reshaping_x = []

for i in range(len(value_x)):
    for j in range(len(value_x[i])):
        reshaping_x.append(value_x[i][j])

"""### 14. Preprocessing Text dengan tokenizer Deep Learning dari Keras dan Scikit-learn"""

tokenizer = Tokenizer()
tokenizer.fit_on_texts(reshaping_x)
sequences = tokenizer.texts_to_sequences(reshaping_x)

sequences_numpy = np.array(sequences)

j = len(sequences_numpy)/len(X)
sequences_numpy = sequences_numpy.reshape(8,2)

vocabulary_size = len(tokenizer.word_counts)

from sklearn.preprocessing import LabelEncoder # Mengonvert hasil y menjadi kode angka
converter = LabelEncoder()
Y_convert = converter.fit_transform(Y)

#from keras.utils.np_utils import to_categorical

#x = sequences_numpy
#y = Y_convert

#y = to_categorical(y , num_classes=vocabulary_size+1)

#seq_len = len(x)

"""### 15. Membuat Model Deep Learning LSTM"""

def create_model(vocabulary_size, seq_len):
    model = Sequential()
    model.add(Embedding(vocabulary_size, 10, input_length=seq_len))
    model.add(LSTM(100, return_sequences=True))
    model.add(LSTM(100))
    model.add(Dense(100, activation='relu'))

    model.add(Dense(vocabulary_size, activation='softmax'))
    
    # Categorical Cross Entropy = Cost Function Classification di Machine Learning
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
   
    model.summary()
    
    return model

# define model
#model = create_model(vocabulary_size+1, seq_len)

"""#### Melakukan training LSTM"""

# Melakukan training LSTM
#model.fit(np.array(x), np.array(y), batch_size=128, epochs=75,verbose=1)

"""### 16. Melakukan Predict Hasil Rekomendasi """

#predict_value = model.predict(converter.fit_transform(Y))
#predict_values = predict_value[0]

#make_integer = []
#for i in range(len(predict_values)):
#    making_integer = round(predict_values[i])
#    make_integer.append(making_integer)

#what_laptop = converter.inverse_transform(make_integer)
#print(what_laptop[0])

"""#### Menyimpan hasil data untuk hasil list rekomendasi"""

#Laptop_first_recommended = {"Nama Laptop" : [] , "Brand" : [] , "Size" : [] , "Processor" : [] , "RAM" : [] , "GPU" : [] , "Storage" : [] , "Harga" : [] , "Link" : []} 

#search_justy = spek.iloc[:,0].values

#for searchlaptop in range(len(search_justy) + 1):
#    if what_laptop[0] == search_justy[searchlaptop]:
#        Laptop_first_recommended["Nama Laptop"].append(search_justy[searchlaptop])
#        Laptop_first_recommended["Brand"].append(spek.iloc[searchlaptop,1])
#        Laptop_first_recommended["Size"].append(spek.iloc[searchlaptop,2])
#        Laptop_first_recommended["Processor"].append(spek.iloc[searchlaptop,3])
#        Laptop_first_recommended["RAM"].append(spek.iloc[searchlaptop,4])
#        Laptop_first_recommended["GPU"].append(spek.iloc[searchlaptop,5])
#        Laptop_first_recommended["Storage"].append(spek.iloc[searchlaptop,6])
#        Laptop_first_recommended["Harga"].append(spek.iloc[searchlaptop,9])
#        Laptop_first_recommended["Link"].append(spek.iloc[searchlaptop,8])
#        break

#data_laptop = pd.DataFrame(Laptop_first_recommended)


#result = data_laptop.to_json(orient="records")
#parsed = json.loads(result)
#json.dumps(parsed , indent = 4)
#with open('Data_rekomendasilaptop.json' , 'w') as f:
#    json.dump(parsed,f)

#openfile = json.loads(open('Dataset Chatbot Laptop.json').read())