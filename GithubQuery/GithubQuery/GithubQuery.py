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
    "html_url",
     "stargazers_count",
     "watchers_count",
     "forks_count"
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


#print([{"html_url": item["html_url"], "Forks": item["forks_count"]} for item in response["items"]])
mydict = [{key:item[key] for key in keys} for item in response["items"]]
jprint(mydict)
#jprint(response)
#print(response["items"])
#print(response["items"][3]["html_url"])
#print(getList(response["items"][3]))
#print(getList(response))

#for key in keys:
#    print('{key}:\t{value}'.format(
#            key=key,
#            value=response[key]
#        )
#    )
