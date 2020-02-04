import requests
from requests.auth import HTTPDigestAuth
import json

MyOauth2Token = 'd9799af140fe1be693a8ab74584e8f6e009a463f'
url = "https://api.github.com/search/repositories?q"


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

headers = { 'Authorization' : 'token ' + MyOauth2Token }

#Which properties are needed
keys = [
    "html_url",
     "stargazers_count",
     "watchers_count",
     "forks_count"
]

#qeuery parameters
queryParams = 'maven2+in:readme'
parameters = {
    "page": 2,
    "q": queryParams
    }


with requests.Session() as s:

    s.headers.update(headers)
    resp = s.get(url, params=parameters)
    #jprint(resp.json())

response = resp.json()


#filter results
FilteredResults = [{key:item[key] for key in keys} for item in response["items"]]
jprint(FilteredResults)
