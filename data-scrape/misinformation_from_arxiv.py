import requests
import json
import bs4

URL = "http://export.arxiv.org/api/query?search_query=all:misinformation&max_results=3000"
RESULTSFILE = 'misinformation_arxiv_parsed.json'

def fetch_data():
    r = requests.get(URL)
    with open('arxiv_response.xml', 'w+') as f:
        f.write(r.text)

        
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


def get_paper_contents(link):
    link = link.replace('/abs/', '/html/')
    print(link)
    data = requests.get(link)
    return bs4.BeautifulSoup(data.text, 'html.parser').get_text()


def main():
    #fetch_data()
    data = load_data()
    results = []
    papers = data.find_all('entry')
    for i, paper in enumerate(papers):
        if i % 10 == 0:
            print(f'Loading paper {i}')
        results.append(
            construct_result_for_paper(paper)
        )

    with open(RESULTSFILE, 'w+') as f:
        f.write(json.dumps(results))


if __name__ == '__main__':
    main()
        
    
