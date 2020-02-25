"""
This module collects github project and commit urls whose are also avaible in Maven Central
"""

__version__ = "0.1"
__author__ = "Bence Fazekas"

import requests
from requests.auth import HTTPDigestAuth
import json
import itertools
import csv
from time import sleep

MyOauth2Token = 'd9799af140fe1be693a8ab74584e8f6e009a463f'
headers = { 'Authorization' : 'token ' + MyOauth2Token }
CommitProperties = [
        "html_url",        
        "url",
         "parents",
         "sha",
         "commit"
    ]

def getDictKeys(dict): 
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
    """collects the github repository informations via Github API"""
    
    url_repo = "https://api.github.com/search/repositories?q"
    #Which properties are needed
    keys_repo = [
        "html_url",
        "url",
         "stargazers_count",
         "watchers_count",
         "forks_count",
         "commits_url"
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
            resp = s.get(url_repo, params=parameters)
            jprint(resp.json())
            #if the sessions is OK
            if resp.status_code == 200 and len(resp.json())>0:
                resultlist.append([{key:item[key] for key in keys_repo} for item in resp.json()["items"]])
                sleep(1)
            #break if Github deny more result
            else:
                break

    #merge the lists
    resultlist = list(itertools.chain.from_iterable(resultlist))
    return resultlist


def GetCommitList(RepoDict):
    """
    collects all the commits of one git repo
    input: A Repo's dictionary
    output: commits containing 'fix' or 'bug' keywords as a dictianary
    """
    #qeuery parameters
    queryParams = 'bug+in:message'

    resultlist = []
    for i in range(2):
    #for i in itertools.count():
        with requests.Session() as s:
            parameters = {
                "page": i
                ,"q": queryParams
                }
            s.headers.update(headers)
            #print(RepoDict["commits_url"][:-6])
            resp = s.get(RepoDict["commits_url"][:-6], params=parameters)

            #jprint(resp.json())
            #if the sessions is OK
            if resp.status_code == 200 and len(resp.json())>0:
                #print(getDictKeys(resp.json()[0]))
                resultlist.append([{key:item[key] for key in CommitProperties} for item in resp.json()])#if "bug" in item["commit"]["message"]
                sleep(0.05)
            #break if Github deny more result
            else:
                break

    resultlist = list(itertools.chain.from_iterable(resultlist))
    return resultlist


def AddParents(CommitList):
    """
        Gets the parents of the commits in a list, 
        input: List of commit dictionaries
        output: list of tuples containing commit dictionaries  (Fixed, Parent)
        NOTE: pairs, because multiple parents are meaning merges
    """
    resultlist = []
    for item in CommitList:
        #currently merges are out from our scope
        if len(item["parents"])==1:
            with requests.Session() as s:
                    s.headers.update(headers)
                    resp = s.get(item["parents"][0]["url"])
                    resultlist.append(item)
                    resultlist.append({key:item[key] for key in CommitProperties})
    return resultlist

def GetTree(TreeUrl):
    """
    Gets the list of files in the repo's (actual commit) main directory
    NOTICE: later can be used to get all files recursively, this feuture is currently not needed
    input: A tree's url
    output: the content of the needed directory
    """
    with requests.Session() as s:        
        s.headers.update(headers)
        resp = s.get(TreeUrl)
        return resp.json()
    #CommitDict["commit"]["tree"]["url"]

def FilterCommits(CommitList):
    """
    Filters the commits based on the existence of the pom.xml file
    input: a list of commits
    output: filetered list of commits
    """
    resultlist = []
    
    #for item in CommitList:  
    cond = False
    Tree = GetTree(CommitList[0]["commit"]["tree"]["url"])
    #jprint(Tree)

    print(type(Tree))
    if type(Tree) is dict and Tree is not {}:
        try:
            for file in Tree["tree"]:
                if file["path"]=="pom.xml":
                    #if the commit contains a pom.xml file, then we need it
                    resultlist.append(item)
                    return CommitList
                #if the latest version doesn't contains the pom.xml file, 
          
        except :
            pass
            
    return []


#RepoTest
#jprint(len(GetRepoList()))
#Commit Test
#jprint(GetCommitList(GetRepoList()[-1]))
#GetCommitList(GetRepoList()[0])
#ParentTest
#jprint(AddParents(GetCommitList(GetRepoList()[15])))
#TreeTest
#jprint(GetTree(GetCommitList(GetRepoList()[5])[1])["commit"]["tree"]["url"])
#FilterTest


if True:
    resultlist = []
    mylist = GetRepoList()

    myNum = 1
    for item in mylist:
        if myNum>5:
            break
        resultlist.append(FilterCommits(GetCommitList(item)))
        jprint(resultlist[-1])

    resultlist = list(itertools.chain.from_iterable(resultlist))
    resultlist = AddParents(resultlist)

    #writes the results to a csv, easier to handle
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    jprint(resultlist)
    with open('people.txt', 'w') as output_file:
        for item in resultlist:
            output_file.write(item["html_url"]+"\n")
       #json.dump(resultlist, output_file)