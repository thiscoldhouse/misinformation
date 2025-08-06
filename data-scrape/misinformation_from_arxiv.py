from pprint import pprint
import requests
import urllib
import json
import bs4
import time
import PyPDF2
import io
import jellyfish

# Notes:
# Script naively assumes that RESULTSFILE is the
# in-progress save of whichever raw_data it is
# currently working from.
# @TODO: Create some metadata structure to avoid
# this


URL = "http://export.arxiv.org/api/query?search_query=all:misinformation&start={start}&max_results=5000"
RESULTSFILE = 'misinformation_arxiv_parsed.json'
ARXIV_RESPONSE_FILE = 'arxiv_response.xml'


class ForbiddenException(Exception):
    pass


class SkipException(Exception):
    pass


def fetch_and_save_raw_data_from_arxiv():
    xml = []
    i = 0
    while True:
        url = URL[:].format(start=i)
        print(f'Fetching {i} page at {url}')
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
        }        
        response = requests.get(URL, headers=headers)
        print(f'Response code: {response.status_code}')
        if response.status_code == 200:
            xml.append(response.text)
        else:
            break
        
    with open(ARXIV_RESPONSE_FILE, 'w+') as f:
        f.write(''.join(xml))

        
def load_in_progress_results_from_file():
    try:
        with open(RESULTSFILE, 'r') as f:
            data = json.loads(f.read())
            data = [] if data is None else data
            return data
    except Exception as e:
        print('=============')
        print('Failed to load old results with error {e}')
        print('Starting from scratch')
        print('=============')        
        return []

        
def save_results(results, final=False):
    fname = RESULTSFILE
    if final:
        fname = f'final_{fname}'
    with open(fname, 'w+') as f:
        f.write(json.dumps(results))
    
    
def load_data_from_file():
    data = None
    with open(ARXIV_RESPONSE_FILE, 'r+') as f:
        data = f.read()

    data = bs4.BeautifulSoup(data, 'xml')
    return data


def fetch_and_parse_paper(paper):
    link = paper.find_all('link', {'type':"application/pdf"})
    assert(len(link) == 1)    
    link = link[0]['href']

    doi = None
    try:
        doi = paper.find_all('doi')[0].contents[0]
    except IndexError as e:
        pass
    
    data = {
        'id': paper.find_all('id')[0].contents[0],
        'title': paper.find_all('title')[0].contents[0],
        'contents': get_paper_contents(link),
        'doi': doi
    }    
    data['citations'], data['doi'] = get_paper_citations(
        data['id'],
        data['title'],
        data['contents'],
        doi
    )
    return data
        

def get_paper_citations(id_, title, contents, doi):
    title = ' '.join(title.split())
    print(f'DOI is {doi}')
    
    headers = {
        'User-Agent': 'Alejandro Ruiz (mailto:alejandro.ruiz@uvm.edu)'
    }
            
    # First will try to get by DOI. If any of that fails,
    # we fall back to a title match
    data = None    
    if doi is not None:
        url = 'https://api.crossref.org/works/{doi}/agency'
        cf = requests.get(
            url[:].format(
                doi=urllib.parse.quote_plus(doi),
            ),
            headers=headers,            
        )
        if cf.status_code == 200:
            cfdata = cf.json()        
            crossref_doi = None
            try:
                crossref_doi = cfdata['message']['DOI']
            except IndexError as e:
                print('==========')
                print(f'Failed to find crossref doi with response:')
                print(cfdata)
                print('==========')

            if crossref_doi is not None:
                url = 'https://api.crossref.org/works/{doi}&select=DOI,title,reference'
                cf = requests.get(
                    url[:].format(
                        doi=urllib.parse.quote_plus(doi)
                    ),
                headers=headers
                )
                if cf.status_code == 200:
                    cfdata = cf.json()
                    data = cfdata['message']['items'][0]['reference']
                    doi = crossref_doi
                    data = fill_out_citations(data)
                    return data, doi
            
    if data is None:
        url = 'https://api.crossref.org/works?query.bibliographic={title}&select=DOI,title,reference'
        cf = requests.get(
            url[:].format(
                title=urllib.parse.quote_plus(title)
            ),
            headers=headers,            
        )
        if cf.status_code != 200:
            print(
                f'Skipping! Status code {cf.status_code}'
            )
            raise SkipException()
        
        cfdata = cf.json()
        for i, item in enumerate(cfdata['message']['items']):
            try:
                returned_title = item['title'][0]
            except KeyError as e:
                print('Found item with no title:')
                print(item)
                continue
            
            distance = jellyfish.levenshtein_distance(
                returned_title.lower(),
                title.lower()
            )
            if distance <= 5:
                print('Matched!')
                doi = item.get('DOI')
                data = item.get('reference')
                data = data or []
                data = fill_out_citations(data)                
                return data, doi
        
    raise SkipException()

    

def get_pdf_contents(pdf_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
    }
    response = requests.get(url=pdf_url, headers=headers)
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(response.content))
    except Exception as e:
        raise SkipException(e)
    num_pages = len(reader.pages)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        full_text.append(text)
        
    return ''.join(text)


def get_paper_contents(link, retry=0):
    print(f'Getting link {link}')
    text = get_pdf_contents(link)
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
        
    return text


def get_html_from_arxiv(link, retry=0):
    # not currently used for anything
    raise NotImplemented()
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


def parse(data, previous_results=[]):
    papers = data.find_all('entry')
    # trim papers for which we already have results from
    # previous scrape attempt
    papers = papers[len(previous_results):]    
    results = previous_results[:]
    previous_results_length = len(results)
    print(f'Total papers to fetch:{len(papers)}')
    try:
        for i, paper in enumerate(papers):
            assert(len(results) == i + previous_results_length)
            try:
                results.append(
                    fetch_and_parse_paper(paper)
                )
            except SkipException as e:
                print('Skipping!')
                results.append(None)

            if i % 50 == 0:
                save_results(results)
                
        save_results(results, final=True)
                
    except Exception as e:
        print('Something happened. Saving what we have then re-raising.')
        save_results(results)
        raise

    


# ================================================================== #
# Things below this line were added when I realized that the citations
# didn't have full data
# ================================================================== #

# def get_doi_by_title(title):
#     print(f'Fetching {title}')
#     url = 'https://api.crossref.org/works?query.bibliographic={title}&select=DOI,title'
#     cf = requests.get(
#         url[:].format(
#             title=urllib.parse.quote_plus(title)
#         ),
#         headers={
#             'User-Agent': 'Alejandro Ruiz (mailto:alejandro.ruiz@uvm.edu)'
#         }
#     )
#     if cf.status_code == 200:
#         cfdata = cf.json()
#         for i, item in enumerate(cfdata['message']['items']):
#             try:
#                 returned_title = item['title'][0]
#             except KeyError as e:
#                 print('Found item with no title:')
#                 print(item)
#                 continue
            
#             distance = jellyfish.levenshtein_distance(
#                 returned_title.lower(),
#                 title.lower()
#             )
#             if distance <= 5:
#                 print('Matched!')
#                 doi = item.get('DOI')
#                 print(f'DOI: {doi}')
#                 return doi
        
#     else:
#         print(f'Failed to find by title with status {cf.status_code}')

    
def get_title_by_doi(doi):
    url = 'https://api.crossref.org/works/{doi}/agency'
    cf = requests.get(
        url[:].format(
            doi=urllib.parse.quote_plus(doi),
        ),
        headers={
            'User-Agent': 'Alejandro Ruiz (mailto:alejandro.ruiz@uvm.edu)'
        }
    )
    if cf.status_code != 200:
        print(f'Failed to find by doi. Crossref_doi lookup failed: {cf.status_code}')
        return

    cfdata = cf.json()        
    crossref_doi = None    
    try:
        crossref_doi = cfdata['message']['DOI']
    except IndexError as e:
        pass
    
    if crossref_doi is not None:
        url = 'https://api.crossref.org/works/{doi}'.format(
                doi=urllib.parse.quote_plus(doi)
            )
        cf = requests.get(
            url,
            headers={
                'User-Agent': 'Alejandro Ruiz (mailto:alejandro.ruiz@uvm.edu)'
            }
        )
        if cf.status_code == 200:
            cfdata = cf.json()
            title = cfdata['message']['title'][0]
            return title

    
def fill_out_citations(citations):            
    for j, citation in enumerate(citations):
        if 'title' not in citation.keys() and 'DOI' in citation.keys():                
            citations[j]['title'] = get_title_by_doi(citation['DOI'])
    return citations
            
        
def fill_out_citations_after():
    data = load_in_progress_results_from_file()
    print(f'Data amount: {len(data)}')
    for i, row in enumerate(data):
        if row is None:
            continue
        for j, citation in enumerate(row['citations']):
            if 'title' not in citation.keys() and 'DOI' in citation.keys():                
                data[i]['citations'][j]['title'] = get_title_by_doi(citation['DOI'])
            
    with open('data_with_titles.json', 'w+') as f:
        f.write(json.dumps(data))

    
def main():
    # comment out top fxn call to work from
    # pre-downloaded file
    #fetch_and_save_raw_data_from_arxiv()
    data = load_data_from_file()
    results = load_in_progress_results_from_file()
    print(f'Preloaded results: {len(results)}')
    results = parse(data, previous_results=results)
    save_results(results)

    
if __name__ == '__main__':
    main()
        
    
