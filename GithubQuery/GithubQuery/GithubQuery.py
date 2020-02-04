import requests
from requests.auth import HTTPDigestAuth
import json

MyOauth2Token = 'd9799af140fe1be693a8ab74584e8f6e009a463f'
url = "https://api.github.com/search/repositories?q"



headers = { 'Authorization' : 'token ' + MyOauth2Token }

queryParams = 'maven2+in:readme'
parameters = {
    "page": 2,
    "q": queryParams
    }


with requests.Session() as s:

    s.headers.update(headers)
    resp = s.get(url, params=parameters)
    jprint(resp.json())

