'''
The Pitt API, to access workable data of the University of Pittsburgh
Copyright (C) 2015 Ritwik Gupta

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import subprocess
import math
import requests
import grequests
import multiprocessing

from joblib import Parallel, delayed
from bs4 import BeautifulSoup


requests.packages.urllib3.disable_warnings()


def _get_person_url(query, i):
    url = "https://m.pitt.edu/people/search.json?search=Search&filter={0}&_region=kgoui_Rcontent_I0_Rcontent_I0_Ritems&_object_include_html=1&_object_js_config=1&_kgoui_page_state=8c6ef035807a2a969576d6d78d211c78&_region_index_offset={1}&feed=directory&start={2}".format(query, str(i*10), str(i*10))
    response_obj = requests.get(url, verify=False)
    response = response_obj.json()["response"]["contents"]

    local_url_list = [x["fields"]["url"]["formatted"] for x in response]
    local_url_list = ["https://m.pitt.edu" + x.replace("\\", "") for x in local_url_list if "&start" not in x]

    return local_url_list


def get_person(query, max_people=10):
    n_cores = multiprocessing.cpu_count()

    query = query.replace(' ', '+')
    url_list = Parallel(n_jobs=n_cores)(delayed(_get_person_url)(query, i) for i in range(int(math.ceil(max_people/10.0))))
    url_list = [item for l_list in url_list for item in l_list]  # flatmap

    results = [grequests.get(u, verify=False) for u in url_list]
    people_info = grequests.imap(results)   # make requests
    persons_list = []
    for person in people_info:
        person_dict = {}
        soup = BeautifulSoup(person.text, 'html.parser')
        name = soup.find('h1', attrs={'class': 'kgoui_detail_title'})
        person_dict['name'] = str(name.get_text())
        for item in soup.find_all('div', attrs={'class': 'kgoui_list_item_textblock'}):
            if item is not None:
                person_dict[str(item.div.get_text())] = str(item.span.get_text())
        persons_list.append(person_dict)
        if len(persons_list) >= max_people:
            return persons_list   # only return up to amount specified
    return persons_list
