import json
import jellyfish
import networkx as nx
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

DATAFILE = 'misinformation_arxiv_parsed.json'


def load_data():
    with open(DATAFILE, 'r+') as f:
        return json.loads(f.read())

            
def find_edges(paper, possible_citation):
    edges = []
    for citation in paper['citations']:
        citation_doi = citation.get('doi')
        pc_doi = possible_citation.get('doi')

        if citation_doi is not None and pc_doi is not None:
            if citation_doi == pc_doi:
                print('----------------------')                
                print('Match by DOI')
                print('----------------------')
                
                edges.append((
                    paper['title'],
                    possible_citation['title']
                ))
                continue

        # Even if DOI match failed, we try to match by title
        # in case of inconsistenty in DOI
        citation_title = citation.get('volume-title')
        pc_title = possible_citation.get('title')
        if citation_title is not None and pc_title is not None:
            citation_title = ' '.join(
                citation_title.split().lower().rstrip().lstrip()
            )
            possible_citation_title = ' '.join(
                pc_title.split().lower().rstrip().lstrip()
            )
            if jellyfish.levenshtein_distance(
                    citation_title,
                    possible_citation_title
            ) < 5:
                edges.append((
                    paper['title'],
                    possible_citation['title']
                ))
                print('----------------------')                
                print('Match!')
                print(citation_title)
                print(possible_title)
                print('----------------------')

    return edges


def main():
    data = load_data()
    data = [thing for thing in data if thing is not None]
    nodes = []
    edges = []
    edges_with_dave = []
    hits = 0
    for i, paper in enumerate(data):
        print(i)
        if 'mediabiasfactcheck.com' in paper['contents'].lower():
            edges_with_dave.append(
                ('mediabiasfactcheck.com', paper['title'])
            )

        nodes.append(paper['title'])
        for possible_citation in data:
            edges.extend(
                find_edges(paper, possible_citation)
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
        
        
    
