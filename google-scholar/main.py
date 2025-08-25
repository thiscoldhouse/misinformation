from scholarly import scholarly
import string
import io
import PyPDF2
import json
import requests
import os
from nltk import tokenize, FreqDist
import itertools
from collections import Counter

import pdb
import pprint


papers_dir = 'papers_data/'


def get_raw_data_from_web():
    search = scholarly.search_pubs_custom_url(
        '/scholar?q=%22mediabiasfactcheck.com'
    )
    data = []
    for i, item in enumerate(search):
        data.append(item)        
        if i % 20 == 0:
            print(f'Saving progress at {i}')
            all_data = load_data_from_file()
            all_data.extend(data)
            with open('data.json', 'w+') as f:
                f.write(json.dumps(all_data))
            data = []
            

def load_data_from_file():
    print('Loading data from file')
    with open('data.json', 'r') as f:
        return json.loads(f.read())

def get_pdf_text_from_url(pdf_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
    }
    response = requests.get(
        url=pdf_url, headers=headers, timeout=120
    )
    reader = PyPDF2.PdfReader(io.BytesIO(response.content))
    num_pages = len(reader.pages)
    all_text = []
    for page in reader.pages:
        text = page.extract_text() 
        all_text.append(text)
        
    return '\n'.join(all_text)


def extract_data_from_google_scholar_query(data):
    def save(papers, i):
        print(f'Saving at {i}')            
        with open(f'{papers_dir}{i}.json', 'w+') as f:
            f.write(json.dumps(papers))

    papers = []
    i = 0
    for paper in data:
        if 'eprint_url' in paper.keys():
            try:
                pdf_data = get_pdf_text_from_url(
                    paper['eprint_url']
                )
            except Exception as e:
                print(f'Failed to get eprint url with exception:')
                print(e)
                continue
            
            papers.append({
                'title': paper['bib']['title'],
                'year': paper['bib']['pub_year'],
                'pdf_data': pdf_data,
                'raw_data': paper,
            })
            if i % 10 == 0 and i > 1:
                save(papers, i)    
                papers = []
                
            print(i)
            i += 1

    save(papers, i)


def load_paper_data_from_files():
    papers = []
    for fname in os.listdir(papers_dir):
        filename = os.fsdecode(fname)
        print(f'Opening {fname}')
        with open(f'{papers_dir}{filename}', 'r') as f:
            papers.extend(json.loads(f.read()))
            
    return papers


def analyze(paper):
    def clean_sentence(sentence):
        sentence = ' '.join(sentence.split())
        sentence.replace('- ', '')
        return sentence.lower()
    
    trigger_words = [
        'mediabiasfactcheck.com',
        'media bias fact check',
        'media bias/fact check',
    ]
    lookahead = 5
    tokenized = tokenize.sent_tokenize(paper['pdf_data'])
    results = []
    for i, sentence in enumerate(tokenized):
        sentence = clean_sentence(sentence)
        for word in trigger_words:
            if word in sentence:
                results.append('. '.join([                    
                    clean_sentence(sentence)
                    for sentence in tokenized[i-lookahead : i+lookahead]
                ]))
    return results

                
def main():
    #get_raw_data_from_web()
    #data = load_data_from_file()
    #extract_data_from_google_scholar_query(data)
    data = load_paper_data_from_files()
    results = []
    
    for i, paper in enumerate(data):
        print(i)
        results.append(analyze(paper))
        if i > 20:
            break

    flatwords = [
        x
        for xs in results
        for x in xs
    ]
    flatwords = ' '.join(flatwords)
    flatwords = flatwords.translate(
        str.maketrans('', '', string.punctuation)
    )
    counter = Counter(' '.join(flatwords)).most_common()

    print(counter)
    import pdb; pdb.set_trace()

if __name__ == '__main__':
    main()
