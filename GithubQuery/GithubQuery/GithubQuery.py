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
from queue import Queue 
from threading import Thread
import concurrent.futures

#FLAG, marked for extermination
import random
import string

#FLAG
MyOauth2Token = 'd9799af140fe1be693a8ab74584e8f6e009a463f'
headers = { 'Authorization' : 'token ' + MyOauth2Token }

 #Which properties are needed
CommitProperties = [
        "html_url",                
         "parents",
         "sha",
         "commit",
         "url"
    ]
RepoProperties = [
        "name",
        "owner",
        "html_url",        
         "stargazers_count",
         "watchers_count",
         "forks_count",
         "commits_url",
         "url"
    ]



DisplayableRepoProperties = [
        "name",   
        "forks_count",
        "stargazers_count",
        "watchers_count",  
        "html_url",
        "url"
    ]
DisplayableCommitProperties = [
        "sha",
        "html_url",
        "url"
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

def GetRepoList(in_q = None, values=None):
    """collects the github repository informations via Github API"""
    if values != None:
        headers = { 'Authorization' : 'token ' + values["txtbox_oauth2token"] }
    else:
        headers = { 'Authorization' : 'token ' + MyOauth2Token }
    
    url_repo = "https://api.github.com/search/repositories?q"
    
   
    
    #qeuery parameters
    queryParams = 'https://repo1.maven.org/+in:readme'
    if values != None:
        queryParams=values["txtbox_queryparam"]
    resultlist = []

    #loop until Github max query limit
    max_progress = 0
    for i in range(1, 2):
    #for i in itertools.count(1):
        with requests.Session() as s:
            parameters = {
                "page": i,
                "q": queryParams
                }
            
            s.headers.update(headers)
            resp = s.get(url_repo, params=parameters)
            print("--------")
            print(resp.status_code)
            #jprint(resp.json())
            print("--------")
            #if the sessions is OK
            if resp.status_code == 401:
                return "Error code 401: please check the Ouath2Token"
            if resp.status_code == 200 and len(resp.json())>0:
                resultlist.append([{key:item[key] for key in RepoProperties} for item in resp.json()["items"]])
                if in_q is not None:
                    max_progress=resp.json()['total_count']/30
                    if max_progress > 34: max_progress=34
                    #print(max_progress)
                    in_q.put((i, max_progress))
                sleep(1)
            #break if Github deny more result
            else:                
                print(i)
                in_q.put((max_progress, max_progress))
                break

    #merge the lists

    resultlist = list(itertools.chain.from_iterable(resultlist))
    return resultlist


def GetCommitList(RepoDict, values=None):
    """
    collects all the commits of one git repo
    input: A Repo's dictionary
    output: commits containing 'fix' or 'bug' keywords as a dictianary
    """
    #qeuery parameters

    queryParams = 'bug+in:message'
    if values != None:
        headers = { 'Authorization' : 'token ' + values["txtbox_oauth2token"] }
        if not values["ChBox_DeafultParams"]:
            queryParams = values["txtbox_commitmessage"]
    else:        
        headers = { 'Authorization' : 'token ' + MyOauth2Token }

    resultlist = [[]]
    for i in range(1,2):
    #for i in itertools.count(1):
        with requests.Session() as s:
            parameters = {
                "page": i
                ,"q": queryParams
                }
            s.headers.update(headers)
            #print(RepoDict["commits_url"][:-6])
            resp = s.get(RepoDict["commits_url"][:-6], params=parameters)
            #jprint(resp.json())
            if resp.status_code == 401:
                return "Error code 401: please check the Ouath2Token"
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


def AddParents(CommitList,in_q = None):
    """
        Gets the parents of the commits in a list, 
        input: List of commit dictionaries
        output: list of tuples containing commit dictionaries  (Fixed, Parent)
        NOTE: pairs, because multiple parents are meaning merges
    """
    resultlist = []
    count = 0
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
                        if in_q is not None:
                            in_q.put((count, len(CommitList)))
                    
                            
                except :
                    print("Error")
        count = count+1
    if in_q is not None:
        in_q.put(( len(CommitList), len(CommitList)))
    sleep(1)
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

def FilterCommits(CommitList, values=None):
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








def Gui_GetRepositories(window, values, phase):    
    q = Queue()
    RepoList = None
    #FLAG
    print("btn_getrepos")
    print(values)
    #txt_label  = window.FindElement('lbl_Progbar1')
    window.Finalize()
    window['Progbar2'].update_bar(phase[0],  phase[1])   
    window['lbl_Progbar2'].update(("Phase: "+str(phase[0])+"/"+str(phase[1])+" Getting Repositories"))
    window['lbl_Progbar1'].update("Starting the query, please stand by")
    window.Finalize()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(GetRepoList, q, values)
        progress = (-1, -1)
        while not future.done():
            if (-1,-1) != progress:
                window.Finalize()
                window['lbl_Progbar1'].update(("Getting Repositories, progress: "+str(progress[0])+"/"+str(progress[1])))
                
                window.Finalize()
                #txt_label.Update('Getting Repositories {}/{}')
                window['Progbar1'].update_bar(progress[0], progress[1])
                
            #print(i)
            if not q.empty():
                progress = q.get()
        result = future.result()
        if type(result) is not list:
            window.Finalize()
            window['lbl_Progbar1'].update(result)
        else:
            RepoList = result
        with q.mutex:
            q.queue.clear()
        jprint(result)
        return RepoList


def Gui_GetCommits(window, values, RepoList):
    CommitList=[]
    if RepoList != None:
        print(RepoList)
    else:
        phase=(1, 3)
        RepoList=Gui_GetRepositories(window, values, phase)

    count = 1
    if RepoList != None:    
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for item in RepoList:     
                window.Finalize()
                window['lbl_Progbar2'].update(("Phase: "+str(2)+"/"+str(3)+" Getting Commits"))
                window['Progbar2'].update_bar(2, 3)
                window['lbl_Progbar1'].update("Starting the query, please stand by")
                future = executor.submit(GetCommitList,item, values)
                while not future.done():
                    window.Finalize()
                    window['lbl_Progbar1'].update(("Getting Commits, progress: "+str(count)+"/"+str(len(RepoList))))
                    window['Progbar1'].update_bar(count, len(RepoList))
                result=future.result()
                if type(result) is not list:
                    window.Finalize()
                    window['lbl_Progbar1'].update(result)
                    break
                future2 = executor.submit(FilterCommits,result, values)
                while not future2.done():
                    window.Finalize()
                    window['lbl_Progbar1'].update(("Filtering Commits, progress: "+str(count)+"/"+str(len(RepoList))))
                    window['Progbar1'].update_bar(count+1,  len(RepoList))      
                result = future2.result()
                count=count+1
                CommitList.append(result)
            CommitList = list(itertools.chain.from_iterable(CommitList))
            if values["ChBox_AddParents"] or values["ChBox_DeafultParams"]:
                
                q = Queue()
                progress = (0, 0)
                window.Finalize()
                window['lbl_Progbar2'].update(("Phase: "+str(3)+"/"+str(3)+" Adding Parents"))
                window['Progbar2'].update_bar(3, 3)
                future3 = executor.submit(AddParents,CommitList, q)
                while not future3.done():
                    if not q.empty():
                        progress = q.get()
                    window.Finalize()
                    window['lbl_Progbar1'].update(("Adding Parents, progress: "+str(progress[0])+"/"+str(progress[1])))
                    window['Progbar1'].update_bar(progress[0],  progress[1])
                    
                CommitList = future3.result()
                window.Finalize()
                #window['lbl_Progbar1'].update(("Adding Parents, progress: "+str(progress[1])+"/"+str(progress[1])))
                #window['Progbar1'].update_bar(progress[1],  progress[1])

    return CommitList
    


def Gui_MainWindow():
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
                  [sg.In(default_text='bug+in:message', size=(80, 1),key='txtbox_commitmessage')],
                  [sg.Text('Oauth2Token:')],
                  [sg.In(default_text=MyOauth2Token, size=(80, 1),key='txtbox_oauth2token')]]


    # layout the Window
    layout = [[sg.Column(col_btn),sg.Column(col_chbox), sg.Column(col_params)],
              [sg.Button('Choose Location',key='btn_location', size = (20, 3)), sg.Text('C:\\Users\\fazon\\source\\repos\\Maven-Github_Database\\GithubQuery'), sg.Button('Start', key='btn_Start', size = (20, 3), pad=((300, 10), 30), font=(15))],
              [sg.Text('', key="lbl_Progbar1",size=(100,1), auto_size_text=True)],
              [sg.ProgressBar(10, orientation='h', size=(96, 20), key='Progbar1')],
              [sg.Text('', key="lbl_Progbar2",size=(100,1), auto_size_text=True)],
              [sg.ProgressBar(3000, orientation='h', size=(96, 20), key='Progbar2')],
              [sg.Cancel()]]

    # create the Window
    window = sg.Window('Custom Progress Meter', layout)
    # loop that would normally do something useful
    i = 0
    j = 0

    #initializing
    RepoList = None
    CommitList = None

    while True:
        i = i+1
    
        # check to see if the cancel button was clicked and exit loop if clicked
        event, values = window.read(timeout=0)
        if event != '__TIMEOUT__':
            print(values)
            if event == 'Cancel' or event is None:
                break    
            elif event == 'btn_getrepos':
                phase=(1, 1)
                RepoList=Gui_GetRepositories(window, values, phase)

            elif event == 'btn_getcommits':
                CommitList=Gui_GetCommits(window, values, RepoList)     
                print("btn_getcommits")
            elif event == 'btn_viewprojects':
                print("btn_viewprojects")
                if RepoList is not None:
                    jprint(RepoList)
            elif event == 'btn_viewcommits':
                print("btn_viewcommits")
                if CommitList is not None:
                   jprint(CommitList)
            elif event == 'btn_Download':
                print("btn_Download")
            elif event == 'btn_location':
                print("btn_location")
            elif event == 'btn_Start':
                print("btn_Start")
       
   

        #így lehet updatelni a max méretet
        #window['Progbar2'].update_bar(i + 1, 10000)


    
    # done with loop... need to destroy the window as it's still open
    window.close()

def copy2clip(txt):
    """Copies a  string to the clipboard
        Windows only!"""
    cmd='echo '+txt.strip()+'|clip'
    return subprocess.check_call(cmd, shell=True)



def MakeTableData(Properties, DictList, CommitMode=False):
    """Unpacks the needed properties from the recieved dictionary
        input:  Properties: List of string which are keys in the dictionaries
                DictList: List of dictionaries                
        output: List of Lists with the needed poroperties
        Note: Properties have to be a subset to saved properties
        """
    #print("asd")
    if len(DictList)==0:
        result= [[]]
    if not CommitMode:
        result = [[item[key] for key in Properties] for item in DictList]
    else:
        result = []
        for item in DictList:
            line = [item["html_url"].split("/")[4]]
            line.append(item["commit"]["message"])
            for key in Properties:
                line.append(item[key])
            result.append(line)
        #headings.append(Properties)
    return result

def Gui_CreatePreview(DictList, Properties, CommitMode=False):
    sg.theme('Dark Blue 13')


    # ------ Make the Table Data ------
   
    data = MakeTableData(Properties, DictList, CommitMode)    
    headings = Properties if not CommitMode else ["Name", "Message"] +Properties
       
   

    # ------ Window Layout ------
    layout = [[sg.Table(values=data[1:][:], headings=headings, max_col_width=25,
                        # background_color='light blue',
                        auto_size_columns=True,
                        display_row_numbers=True,
                        justification='left',
                        num_rows=20,
                        # alternating_row_color='lightyellow',
                        key='-TABLE-',
                        tooltip='List of the Repositories')],
              [sg.Button('Copy url'),sg.Button('Copy html url'), sg.Button('Back')],
              [sg.Text('Read = read which rows are selected')],
              [sg.Text('Change Colors = Changes the colors of rows 8 and 9')]]

    # ------ Create Window ------
    window = sg.Window('The Table Element', layout)

    # ------ Event Loop ------
    while True:
        event, values = window.read()
        print(event, values)
        if event is None:
            break
        if event == 'Copy html url':
            if len(values['-TABLE-'])==1:
                print(values['-TABLE-'][0])
                url=""
                if not CommitMode:
                    url = window['-TABLE-'].Values[values['-TABLE-'][0]][len(Properties)-2]
                else:
                    url = window['-TABLE-'].Values[values['-TABLE-'][0]][len(Properties)]
                print(url)
                copy2clip(url)
        if event == 'Copy url':
            if len(values['-TABLE-'])==1:
                print(values['-TABLE-'][0])
                url=""
                if not CommitMode:
                    url = window['-TABLE-'].Values[values['-TABLE-'][0]][len(Properties)-1]
                else:
                    url = window['-TABLE-'].Values[values['-TABLE-'][0]][len(Properties)+1]
                print(url)
                copy2clip(url)
        elif event == 'Back':
            break

    window.close()

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
#MainWindow()
#hide  the console
#ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

#ProjectPreview
#RepoList=GetRepoList()
resultlist = []
mylist = GetRepoList()
for item in mylist:
    resultlist.append(FilterCommits(GetCommitList(item)))   
    print("MAIn")

resultlist = list(itertools.chain.from_iterable(resultlist))



print(getDictKeys(resultlist[0]))
print(getDictKeys(resultlist[0]["commit"]))
Gui_CreatePreview(resultlist, DisplayableCommitProperties, True)