import requests
import json
import bs4
import time

# Notes:
# Script naively assumes that RESULTSFILE is the
# in-progress save of whichever raw_data it is
# currently working from.
# @TODO: Create some metadata structure to avoid
# this

URL = "http://export.arxiv.org/api/query?search_query=all:misinformation&max_results=3000"
RESULTSFILE = 'misinformation_arxiv_parsed.json'


class ForbiddenException(Exception):
    pass


class SkipException(Exception):
    pass


def fetch_raw_data_from_arxiv():
    r = requests.get(URL)
    with open('arxiv_response.xml', 'w+') as f:
        f.write(r.text)

        
def load_in_progress_results_from_file():
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
    
    
def load_data_from_file():
    data = None
    with open('arxiv_response.xml', 'r+') as f:
        data = f.read()

    return bs4.BeautifulSoup(data, 'xml')


def fetch_and_parse_paper(paper):
    link = paper.find_all('link')[0]
    link = link['href']
    contents = get_paper_contents(link)
    return {
        'id': paper.find_all('id')[0].contents[0],
        'title': paper.find_all('title')[0].contents[0],
        'contents': contents
    }


def get_paper_contents(link, retry=0):
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
    
    import pdb; pdb.set_trace()
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
                print('Backing off for 60 seconds')
                time.sleep(60)        
                return get_paper_contents(link, retry=1)
            if retry == 1:
                print('Backing off for 90 seconds')
                time.sleep(90)        
                return get_paper_contents(link, retry=2)
            if retry == 2:
                print('Bailing')
                raise ForbiddenException()
    
    return {
        'text': bs4.BeautifulSoup(
            data.text, 'html.parser'
        ).get_text(),
        'html': data.text
    }

def parse(data, previous_results=None):
    papers = data.find_all('entry')
    if previous_results is not None:
        # trim papers for which we already have results from
        # previous scrape attempt
        papers = papers[len(results):]
        
    print(f'Total papers to fetch:{len(papers)}')
    try:
        for i, paper in enumerate(papers):
            try:
                if i % 5 == 0 and i > 0:
                    print(f'Loading paper {i}. Taking short break first...')
                    time.sleep(5)
                results.append(
                    fetch_and_parse_paper(paper)
                )
            except SkipException as e:
                pass

            if i % 50 == 0:
                save_results(results)
    except Exception as e:
        print('Something happened. Saving what we have.')
        pass

    
def main():
    # One of these two should be commented out:
    # -- #
    #fetch_raw_data_from_arxiv()
    data = load_data_from_file()
    # -- #
    
    results = load_in_progress_results_from_file()
    print(f'Preloaded results: {len(results)}')
    results = parse(data, previous_results=results)
    save_results(results)

    
if __name__ == '__main__':
    main()
        
    
