"""
This module collects github project and commit urls whose are also avaible in Maven Central
prerequisties: git
"""

__version__ = "0.1"
__author__ = "Bence Fazekas"

import os
import requests
from requests.auth import HTTPDigestAuth
import json
import itertools
import csv
import subprocess
from time import sleep
import PySimpleGUI as sg
import ctypes

#FLAG
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
    #for i in range(1, 3):
    for i in itertools.count(1):
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

    resultlist = [[]]
    #for i in range(1,3):
    for i in itertools.count(1):
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
                ListItem = [{key:item[key] for key in CommitProperties} for item in resp.json() if "bug" in item["commit"]["message"] or "fix" in item["commit"]["message"]]#if "bug" in item["commit"]["message"]
                if ListItem != resultlist[-1]:
                    resultlist.append(ListItem)
                sleep(1)
            #break if Github deny more result
            else:
                break

    resultlist = list(itertools.chain.from_iterable(resultlist))
    #jprint(resultlist)
    
    return ChooseCommits(resultlist, 10)
    return resultlist

def ChooseCommits(CommitList, CommitNumber):
    """
    picks a fixed number of commits from a list based on homogeneous distribution
    input: list of commits
    output: smaller list of commits
    """
    length = len(CommitList)  
    if length<CommitNumber:
        return CommitList
    resultlist=[]
    #resultlist.append(CommitList[0])
    DebugPrint()
    for i in range(CommitNumber):
        print(round(length*0.1*i))
        resultlist.append(CommitList[round(length*0.1*i)])
    #resultlist.append(CommitList[length-1])
    print("Wise choice indeed!")
    #jprint(resultlist)
    DebugPrint()
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
                try:
                    resp = s.get(item["parents"][0]["url"])
                    if resp.status_code == 200 and len(resp.json())>0:                        
                        resultlist.append(item)
                        #jprint(resp.json())
                        NewItem = {key:resp.json()[key] for key in CommitProperties}
                        if NewItem not in CommitList:
                            resultlist.append(NewItem)
                        print("Successful")
                        sleep(1)
                except :
                    print("Error")
                
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
    if CommitList == []:
        print("TOO FEW COMMITS")        
        return []
    resultlist = []
    
    #for item in CommitList:  
    cond = False
    Tree = GetTree(CommitList[0]["commit"]["tree"]["url"])
    #jprint(Tree)

    #print(type(Tree))
    if type(Tree) is dict and Tree is not {}:
        try:
            for file in Tree["tree"]:
                if file["path"]=="pom.xml":
                    #if the commit contains a pom.xml file, then we need it
                    return CommitList
                    #resultlist.append(item)
                
            #if the latest version doesn't contains the pom.xml file, 
          
        except :
            pass
            
    return resultlist

def CollectData():
    resultlist = []
    mylist = GetRepoList()
    for item in mylist:
        resultlist.append(FilterCommits(GetCommitList(item)))   
        #resultlist.append(GetCommitList(item))   
        #jprint(resultlist)
        print("MAIn")

    resultlist = list(itertools.chain.from_iterable(resultlist))
    
    #jprint(resultlist)
    resultlist = AddParents(resultlist)

    #writes the results to a csv, easier to handle
    DebugPrint()
    jprint(resultlist)
    with open('people.txt', 'w') as output_file:
        for item in resultlist:
            html = item["html_url"]
            sha = item["sha"]
            output_file.write(html[:-(len(sha)+len("/commit/"))]+"\n")
            output_file.write(sha+"\n")


def DownloadDatabase(inputpath="C:\\Users\\fazon\\source\\repos\\Maven-Github_Database\\GithubQuery\\GithubQuery\\people.txt", output_path = "E:/Repo"):
    """Downlaod the commits from inputpath to output_path"""
      
    with open(inputpath) as fp:
        count =1
        html = fp.readline()
        sha = fp.readline()
        os.system("E:")  
        while html:
            #removing the \n from the end
            html=html[:-1]
            sha=sha[:-1]
            os.chdir(output_path)

            os.system(f"cd {output_path}")
            os.system(f"git clone -n {html} {count}")
            os.chdir(f"{output_path}/{count}")
            os.system(f"git checkout {sha}")
            os.chdir(output_path)
            count= count+1
            html = fp.readline()
            sha = fp.readline()
            print(count)
            if count > 10:
                break

def DebugPrint():
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    print("################")
    
#RepoTest
#jprint(len(GetRepoList()))
#Commit Test
#jprint(GetCommitList(GetRepoList()[-1]))
#GetCommitList(GetRepoList()[0])
#ParentTest
#jprint(AddParents(GetCommitList(GetRepoList()[15])))
#TreeTest
#jprint(GetTree(GetCommitList(GetRepoList()[5])[1])["commit"]["tree"]["url"])


#Github Query
#CollectData()

#Download the database
#DownloadDatabase()

#UI

#hide  the console
#ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

sg.theme('Dark Blue 13')





 # Column layout      
col_btn = [[sg.Button('GetRepositoires',key='btn_getrepos', size = (20, 3), font=(15))],      
        [sg.Button('GetCommits',key='btn_getcommits', size = (20, 3), font=(15))],      
        [sg.Button('Preview Projects',key='btn_viewprojects', size = (20, 3), font=(15))],
        [sg.Button('Preview Commits',key='btn_viewcommits', size = (20, 3), font=(15))],
        [sg.Button('Download Database',key='btn_Download', size = (20, 3), font=(15))]]      

col_chbox =  [[sg.Text('Search Parameters:')],
        [sg.Checkbox('Use Default parameters', size=(20, 1),  key='ChBox_DeafultParams', default=True)],
        [sg.Checkbox('AddParents', size=(20, 1), key='ChBox_AddParents')],      
        [sg.Checkbox('Search pom.xml', size=(20, 1), key='ChBox_SearchPom')],        
        [sg.Checkbox('Limit Commits', size=(20, 1), key='ChBox_LimitCommits')],
        [sg.Checkbox('Limits Results', size=(20, 1), key='ChBox_Limitresults')]]      

col_params =  [[sg.Text('Query parameters:')],
              [sg.In(default_text='https://repo1.maven.org/+in:readme' ,key='txtbox_queryparam', size=(80, 1))],
              [sg.Text('Commit message filter:')],
              [sg.In(default_text='bug, fix, bugfix', size=(80, 1),key='txtbox_commitmessage')],
              [sg.Text('Oauth2Token:')],
              [sg.In(default_text=MyOauth2Token, size=(80, 1),key='txtbox_oauth2token')]]


# layout the Window
layout = [[sg.Column(col_btn),sg.Column(col_chbox), sg.Column(col_params)],
          [sg.Button('Choose Location',key='btn_location', size = (20, 3)), sg.Text('C:\\Users\\fazon\\source\\repos\\Maven-Github_Database\\GithubQuery'), sg.Button('Start', key='btn_Start', size = (20, 3), pad=((300, 10), 30), font=(15))],
          [sg.Text('A custom progress meter'), sg.Text('', key="lbl_Progbar1")],
          [sg.ProgressBar(1000, orientation='h', size=(96, 20), key='Progbar1')],
          [sg.Text('A custom progress meter'), sg.Text('', key="lbl_Progbar2")],
          [sg.ProgressBar(3000, orientation='h', size=(96, 20), key='Progbar2')],
          [sg.Cancel()]]

# create the Window
window = sg.Window('Custom Progress Meter', layout)
# loop that would normally do something useful
i = 0
j = 0
while True:
    i = i+1
    
    # check to see if the cancel button was clicked and exit loop if clicked
    event, values = window.read(timeout=0)
    if event == 'Cancel' or event is None:
        break
    elif event == 'btn_getrepos':
        print("btn_getrepos")
        GetRepoList()
        print(values)
    elif event == 'btn_getcommits':
        print("btn_getcommits")
    elif event == 'btn_viewprojects':
        print("btn_viewprojects")
    elif event == 'btn_viewcommits':
        print("btn_viewcommits")
    elif event == 'btn_Download':
        print("btn_Download")
    elif event == 'btn_location':
        print("btn_location")
    elif event == 'btn_Start':
        print("btn_Start")
        # update bar with loop value +1 so that bar eventually reaches the maximum
    window['Progbar1'].update_bar(i + 1)
    window['Progbar2'].update_bar(j+ i + 1)
    if i > 1000:
        j= j+i
        i =  0
    if j > 3000:
        j=0

    #így lehet updatelni a max méretet
    #window['Progbar2'].update_bar(i + 1, 10000)


    
# done with loop... need to destroy the window as it's still open
window.close()


    