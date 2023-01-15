from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

tokenizer=RegexpTokenizer(r'\w+')  
en_stopwords=set(stopwords.words('english'))  
ps=PorterStemmer()

def getCleanedText(text):  
    text = text.lower()  
    #tokenize  
    tokens=tokenizer.tokenize(text)
    new_tokens=[token for token in tokens if token not in en_stopwords]  
    stemmed_tokens=[ps.stem(tokens) for tokens in new_tokens]  
    clean_text=" ".join(stemmed_tokens)  
    return clean_text   

def analyze(X_test : list):
    X_train = [
            "CSNB.in provides best news for students",  
            "It is a great platform to start off your CyberSecurityTips image",  
            "Concepts are explained very well",  
            "The articles have some interesting stories",  
            "Some blogs are bad",  
            "Their content can confuse students",
            "This Blog makes no sense",
            "Your knowledge of this domain is greatly presented",
            "Your tip did not work",
            "That is a good tip but only for a small scope",
            "It's a good approach, could be more affordable."
        ]

    # 1 : Positive, 0 : Neutral , -1 : Negative
    y_train = [1,1,0,0,-1,-1,-1,1,-1,0,0]
    
    X_clean = [getCleanedText(j) for j in X_train]
    Xt_clean = [getCleanedText(j) for j in X_test]

    cv=CountVectorizer(ngram_range=(1,2))

    X_vect = cv.fit_transform(X_clean).toarray()
    Xt_vect = cv.transform(Xt_clean).toarray()

    mlb = MultinomialNB()
    mlb.fit(X_vect,y_train)
    y_pred = mlb.predict(Xt_vect)

    return  list(y_pred)

if __name__=="__main__":
    analyze()