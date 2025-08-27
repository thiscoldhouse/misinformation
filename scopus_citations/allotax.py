import os
from py_allotax.generate_svg import generate_svg
import csv
import shifterator as sh

data = None
with open('abstract_cleaned_per_year.csv', 'r') as f:
    data = csv.reader(f)
    data.next()
    new = []
    old = []
    for row in data:
        text = row[1]
        year = row[2]

        if int(year) > 2017:
            new.append(text)
        elif int(year) < 2016:
            old.append(text)


