import requests
from requests.auth import HTTPDigestAuth
import json

MyOauth2Token = 'd9799af140fe1be693a8ab74584e8f6e009a463f'
url = "https://api.github.com/search/repositories?q"


def getList(dict): 
    list = [] 
    for key in dict.keys(): 
        list.append(key) 
          
    return list

def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

headers = { 'Authorization' : 'token ' + MyOauth2Token }


keys = [
     "stargazers_count",
     "watchers_count",
     "forks"
]

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



      
#jprint(response)

print(getList(response["items"][0]))

#for key in keys:
#    print('{key}:\t{value}'.format(
#            key=key,
#            value=response[key]
#        )
#    )
