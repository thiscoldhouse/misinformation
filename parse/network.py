import json
import networkx as nx
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

DATAFILE = 'misinformation_arxiv_parsed.json'


def load_data():
    with open(DATAFILE, 'r+') as f:
        return json.loads(f.read())

    
def parse_references(item):
    html = item['contents']['html']
    soup = BeautifulSoup(html, 'html.parser')
    bib = soup.find_all('ul', {'class': 'ltx_biblist'})
    if len(bib) != 1:
        print('====')
        print(f'Skipping reference parsing for item: {item['title']}')
        print(item['title'])
        print('====')
        return []
    bib = bib[0]
    references = []
    for citation in bib.find_all('li', {'class': 'ltx_bibitem'}):
        possible_titles = citation.find_all(
            'span', {'class': 'ltx_bibblock'}
        )
        possible_titles = [
            pt.get_text().lstrip().rstrip().replace('\n', ' ')
            for pt in possible_titles
        ]
        references.append(
            possible_titles
        )
    return references

        
def find_edges(item, match_item):
    edges = []
    for citation in item['citations']:
        for possible_title in citation:
            cleaned_match = match_item['title'].lstrip().rstrip().replace('\n', ' ').lower()
            if (
                    cleaned_match in possible_title.lower() 
                    # possible_title.lower() in cleaned_match or
                    # cleaned
            ):
                edges.append((
                    item['title'],
                    match_item['title']
                ))
                print('----------------------')
                print('----------------------')                
                print('Match!')
                print(cleaned_match)
                print(possible_title.lower())
                print('----------------------')
                print('----------------------')
                break
                    
    return edges


def main():
    data = load_data()
    nodes = []
    edges = []
    edges_with_dave = []
    hits = 0
    for i, item in enumerate(data):
        print(i)
        if 'mediabiasfactcheck.com' in item['contents']['text'].lower():
            edges_with_dave.append(
                ('mediabiasfactcheck.com', item['title'])
            )
        item['citations'] = parse_references(item)
        nodes.append(item['title'])
        for match_item in data:
            edges.extend(
                find_edges(item, match_item)
            )
            
    data = {
            'nodes': nodes,
            'edges': edges,
            'edges_with_dave': edges_with_dave
        }
    with open('data-for-network.json', 'w+') as f:
        f.write(json.dumps(data))

if __name__ == '__main__':
    main()
        
        
    
