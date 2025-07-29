from scholarly import scholarly
import json
from bs4 import BeautifulSoup
import requests
import PyPDF2
import re
import io

import pprint
    
RAWDATAFILE='data.json'
#DATAFILE = 'saved_data.json'
DATAFILE = 'misinformation_saved_data.json'
DOMAIN = 'mediabiasfactcheck.com'


def get_raw_data_from_web():
    search = scholarly.search_pubs_custom_url(
        '/scholar?q=%22mediabiasfactcheck.com'
    )

    
def load_raw_data_from_file(fname=RAWDATAFILE):    
    with open(fname, 'r') as f:
        return {
            'raw': json.loads(f.read()),
            'has_citation': [],
            'no_citation': []
        }

    
def clean_data(datafile=DATAFILE, get_raw=False):
    data = None
    if get_raw:
        data = load_raw_data_from_file()
    else:
        with open(datafile, 'r') as f:
            data = json.loads(f.read())

    while len(data['raw']) > 0:
        paper = data['raw'].pop(0)
        if paper.get('eprint_url') is None:
            print('==============')
            print('NO EPRINT URL')
            pprint.pprint(paper)
            print('==============')            
            continue
        
        if verify_relevant(paper['eprint_url']):
            data['has_citation'].append(paper)
        else:
            data['no_citation'].append(paper)
            
        with open(datafile, 'w+') as f:
            f.write(json.dumps(data))

            
def verify_relevant(paper_url):
    print(f'Verifying url: {paper_url}...')
    if 'nature.com' in paper_url:
        r = requests.get(paper_url)
        bs = BeautifulSoup(r.text)
        if len(bs.find_all("a", {"class": "u-color-open-access"})) == 1:
            if len(bs.findAll(text='mediabiasfactcheck.com')) > 0:
                return True
            else:                
                return False
            
    if (
            'arxiv.org' in paper_url or
            paper_url.split('.')[-1].lower() == 'pdf' or
            'pdf' in paper_url
    ):
        if verify_source_in_pdf(paper_url):
            return True
        else:                
            return False
            
    
    print('=====')
    print('no plan for verifying this url')
    print(paper_url)

def verify_source_in_pdf(pdf_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
    }
    response = requests.get(url=pdf_url, headers=headers, timeout=120)
    reader = PyPDF2.PdfReader(io.BytesIO(response.content))
    num_pages = len(reader.pages)        
    for page in reader.pages:
        text = page.extract_text() 
        res_search = re.search(DOMAIN, text, re.IGNORECASE)
        if res_search is not None:
            return True
    else:
        return False
            
            
    
    


if __name__ == '__main__':
    clean_data(get_raw=True)
        
            
    
