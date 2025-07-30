import requests
import matplotlib.pyplot as plt
import io
import json
import pandas as pd
import seaborn as sns
import numpy as np


def get_data_from_dave():
    url = "https://media-bias-fact-check-ratings-api2.p.rapidapi.com/fetch-data"

    headers = {
        "x-rapidapi-key": "d23e0e6934msh8536eb775cb9c7dp1857b5jsnea30cbecf20d",
        "x-rapidapi-host": "media-bias-fact-check-ratings-api2.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    with open('data_dump.json', 'w+') as f:
        f.write(response.text)

        
def load_data():
    data = None
    data = json.load(io.open('data.txt', 'r', encoding='utf-8-sig'))
    for line in data:
        print(line['Source'])

    df = pd.DataFrame.from_dict(data)
    df.to_csv('dave.csv', encoding='utf-8', index=False)


def plot_bias_vs_credibility(csv_file='dave.csv'):
    df = pd.read_csv(csv_file)
    
    def convert_bias_to_int(bias):
        bias = bias.lower().lstrip().rstrip()
        if bias == 'least biased':
            return 0
        elif bias == 'left-center':
            return -1
        elif bias == 'left':
            return -2
        elif bias == 'right-center':
            return 1
        elif bias == 'right':
            return 2
        elif bias == 'questionable' or 'conspiracy-pseudoscience':
            return None
        else:
            raise ValueError("Can't convert {} ".format(bias))

    def convert_credibility_to_int(cred):
        try:
            cred = cred.lower().lstrip().rstrip()
        except AttributeError:
            return None
            
        if cred == 'very low':
            return 0
        elif cred == 'low':
            return 1
        elif cred == 'mixed' or cred == 'medium':
            return 2
        # elif cred == 'mostly factual':
        #     return 3    
        elif cred == 'high':
            return 3
        elif cred == 'very high':
            return 4
        else:
            raise ValueError("Can't convert {}".format(cred))

    def convert_factual_reporting_to_int(fr):
        try:
            fr = cred.lower().lstrip().rstrip()
        except AttributeError:
            return None
            
        if cred == 'very low':
            return 0
        elif cred == 'low':
            return 1
        elif cred == 'mixed' or cred == 'medium':
            return 2
        elif cred == 'mostly factual':
            return 3    
        elif cred == 'high':
            return 4
        elif cred == 'very high':
            return 5
        else:
            raise ValueError("Can't convert {}".format(fr))
        

    def clean_column(val):
        return val
        #return val.lstrip.rstrip.lower()
        
    df['Bias'] = df['Bias'].apply(convert_bias_to_int)
    df['Credibility'] = df['Credibility'].apply(convert_credibility_to_int)
    df = df[['Bias', 'Credibility']]
    d = df.dropna(how='any',axis=0)
    count_table = df.groupby(['Credibility', 'Bias']).size().unstack(fill_value=0)

    # Plot the heatmap with annotations
    plt.figure(figsize=(10, 8))
    sns.heatmap(count_table, annot=True, fmt='d', cmap='Reds', cbar_kws={'label': 'Count'})
    plt.title('Bias and Credibility')
    plt.xlabel('Bias')
    plt.ylabel('Credibility')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()
    
if __name__ == '__main__':
    #load_data()
    plot_bias_vs_credibility()

