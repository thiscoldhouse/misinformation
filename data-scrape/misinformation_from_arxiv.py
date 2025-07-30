import requests
import json
import bs4
import time
import random

URL = "http://export.arxiv.org/api/query?search_query=all:misinformation&max_results=3000"
RESULTSFILE = 'misinformation_arxiv_parsed.json'

class ForbiddenException(Exception):
    pass

class SkipException(Exception):
    pass

def fetch_data():
    r = requests.get(URL)
    with open('arxiv_response.xml', 'w+') as f:
        f.write(r.text)

        
def load_results():
    with open(RESULTSFILE, 'r+') as f:
        try:
            return json.loads(f.read())
        except Exception as e:
            print('Failed to load old results with error {e}')
            print('Starting from scratch')
            return []

def save_results(results):
    with open(RESULTSFILE, 'w+') as f:
        f.write(json.dumps(results))
    
    
def load_data():
    data = None
    with open('arxiv_response.xml', 'r+') as f:
        data = f.read()

    return bs4.BeautifulSoup(data, 'xml')


def construct_result_for_paper(paper):
    link = paper.find_all('link')[0]
    link = link['href']
    contents = get_paper_contents(link)
    return {
        'id': paper.find_all('id')[0].contents[0],
        'title': paper.find_all('title')[0].contents[0],
        'contents': contents
    }


def get_paper_contents(link, retry=0):
    link = link.replace('/abs/', '/html/')
    print(link)
    data = requests.get(link)
    if data.status_code != 200:
        print(f'Bad status code {data.status_code}')
        if 'arxiv.org' not in link:
            print(f'{link} is not an arxiv.org link. Skipping')
            raise SkipException()
        if data.status_code != 403:
            print('Skipping. I only know how to handle 403s and 200s')
            raise SkipException()
        
        else:
            if retry == 0:
                time.sleep(60)        
                return get_paper_contents(link, retry=1)
            if retry == 1:
                time.sleep(90)        
                return get_paper_contents(link, retry=2)
            if retry == 2:                
                raise ForbiddenException()
    
    return {
        'text': bs4.BeautifulSoup(
            data.text, 'html.parser'
        ).get_text(),
        'html': data.text
    }


def main():
    #fetch_data()
    data = load_data()
    results = load_results()
    print(f'Preloaded results: {len(results)}')
    papers = data.find_all('entry')

    # trim papers for which we already have results from
    # previous scrape attempt
    papers = papers[len(results):]
    print(f'Total papers to fetch:{len(papers)}')
    try:
        for i, paper in enumerate(papers):
            try:
                if i % 5 == 0 and i !=0:
                    print(f'Loading paper {i}. Taking short break first...')
                    time.sleep(random.randint(2,5))
                results.append(
                    construct_result_for_paper(paper)
                )
            except SkipException as e:
                pass

            if i % 50 == 0:
                save_results(results)
    except Exception as e:
        print('Something happened. Saving what we have.')
        pass

    save_results(results)

if __name__ == '__main__':
    main()
        
    
