"""
This module collects github project and commit urls whose are also avaible in Maven Central
"""

__version__ = "0.1"
__author__ = "Bence Fazekas"

import requests
from requests.auth import HTTPDigestAuth
import json
import itertools
from time import sleep


MyOauth2Token = 'd9799af140fe1be693a8ab74584e8f6e009a463f'
headers = { 'Authorization' : 'token ' + MyOauth2Token }

def getList(dict): 
    """returns all keys from a dictionary as a list"""
    list = [] 
    for key in dict.keys(): 
        list.append(key)           
    return list


def jprint(obj):
    """create a formatted string of the Python JSON object"""
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def GetRepoList():
    #collects the github repository informations via Github API

    
    repo_url = "https://api.github.com/search/repositories?q"
    #Which properties are needed
    keys = [
        "html_url",
         "stargazers_count",
         "watchers_count",
         "forks_count"
    ]
    #qeuery parameters
    queryParams = 'https://repo1.maven.org/+in:readme'

    resultlist = []

    #loop until Github max query limit
    for i in range(2):
    #for i in itertools.count():
        with requests.Session() as s:
            parameters = {
                "page": i,
                "q": queryParams
                }
            s.headers.update(headers)
            resp = s.get(repo_url, params=parameters)
            #if the sessions is OK
            if resp.status_code == 200:
                resultlist.append([{key:item[key] for key in keys} for item in resp.json()["items"]])
                sleep(0.05)
            #break if Github deny more result
            else:
                break

    #merge the lists
    resultlist = list(itertools.chain.from_iterable(resultlist))
    return resultlist

jprint(GetRepoList())