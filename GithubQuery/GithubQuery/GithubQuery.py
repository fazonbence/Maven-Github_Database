"""
This module collects github project and commit urls whose are also avaible in Maven Central
prerequisties: git
"""

__version__ = "0.1"
__author__ = "Bence Fazekas"

import os
import sys
import requests
from requests.auth import HTTPDigestAuth
import json
import itertools
import csv
import subprocess
import multiprocessing as mp
from time import sleep
import PySimpleGUI as sg
import ctypes
from queue import Queue 
from threading import Thread
import concurrent.futures
import tkinter as tk
from tkinter import filedialog
import pathlib
import math


#FLAG
MyOauth2Token = ''
headers = { 'Authorization' : 'token ' + MyOauth2Token }

 #Which properties are needed in the query
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

#Which properties should be displayed
DisplayableRepoProperties = [
        "name",   
        "forks_count",
        "stargazers_count",
        "watchers_count",  
        "html_url",
        "url"
    ]
DisplayableCommitProperties = [        
        "html_url",
        "url"
    ]

def getDictKeys(dict) : 
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
    iterator = itertools.count(1)#loop until Github max query limit
    headers = { 'Authorization' : 'token ' + MyOauth2Token }
    if values != None:
        headers = { 'Authorization' : 'token ' + values["txtbox_oauth2token"] }
        if values["ChBox_LimitRepos"]:
            iterator = range(1, 2)
    else:
        if not values["ChBox_DeafultParams"]:
            headers = { 'Authorization' : 'token ' + MyOauth2Token }
    
    url_repo = "https://api.github.com/search/repositories?q"
    
   
    
    #qeuery parameters
    queryParams = 'https://repo1.maven.org/+in:readme'
    if values != None:
        queryParams=values["txtbox_queryparam"]
    resultlist = []

    
    max_progress = 0
    
    for i in iterator:
        with requests.Session() as s:
            parameters = {
                "page": i,
                "q": queryParams
                }
            
            s.headers.update(headers)
            resp = s.get(url_repo, params=parameters)
            
            #if the sessions is OK
            if resp.status_code == 401:
                return "Error code 401: please check the Ouath2Token"
            if resp.status_code == 200 and len(resp.json())>0:
                resultlist.append([{key:item[key] for key in RepoProperties} for item in resp.json()["items"]])
                if in_q is not None:
                    max_progress=math.ceil(resp.json()['total_count']/30)
                    if max_progress > 34: max_progress=34
                    if values["ChBox_LimitRepos"]: max_progress=1
                    #print(max_progress)
                    if i>max_progress: 
                        break
                    in_q.put((i, max_progress))
                sleep(1)
            #break if Github deny more result
            else:                
                print(i)
                in_q.put((max_progress, max_progress))
                break
            print("Getting Repos "+str(i)+"/"+str(max_progress))

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
    iterator = itertools.count(1)
    #default parameters
    keywordlist = ["bug", "fix"]
    queryParams = 'bug+in:message'

    #parameters from the user
    if values != None:
        headers = { 'Authorization' : 'token ' + values["txtbox_oauth2token"] }
        if not values["ChBox_DeafultParams"]:
            if ',' in values["txtbox_commitmessage"]:
                keywordlist = values["txtbox_commitmessage"].split(",")
               
            else:
                keywordlist = [values["txtbox_commitmessage"]]

            queryParams = '+'.join(keywordlist)+"+in:message"
            
        if values["ChBox_LimitCommits"]:
            iterator = range(1, 2)
    else:        
        headers = { 'Authorization' : 'token ' + MyOauth2Token }

    resultlist = [[]]
    for i in iterator:
        with requests.Session() as s:
            parameters = {
                "page": i
                ,"q": queryParams
                }
            s.headers.update(headers)
            resp = s.get(RepoDict["commits_url"][:-6], params=parameters)
            if resp.status_code == 401:
                return "Error code 401: please check the Ouath2Token"
            #if the sessions is OK
            if resp.status_code == 200 and len(resp.json())>0:        
                ListItem = [{key:item[key] for key in CommitProperties} for item in resp.json() for substr in keywordlist if substr in item["commit"]["message"]]                

                if ListItem != resultlist[-1]:
                    resultlist.append(ListItem)
                sleep(1)
            #break if Github deny more result
            else:
                break
    #merging the lists
    resultlist = list(itertools.chain.from_iterable(resultlist))
    
    return ChooseCommits(resultlist, 10)

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
    DebugPrint()
    for i in range(CommitNumber):
        print(round(length*0.1*i))
        resultlist.append(CommitList[round(length*0.1*i)])
    print("The Commits have been chosen!")
    DebugPrint()
    return resultlist


def AddParents(CommitList,in_q = None):
    """
        Gets the parents of the commits in a list, 
        input: List of commit dictionaries
        output: List of commit dictionaries with parents
        NOTE: multiple parents are possible due to merges
    """
    resultlist = []
    count = 0
    for item in CommitList:
        resultlist.append(item)
        if len(item["parents"])==1:
            with requests.Session() as s:
                s.headers.update(headers)
                try:
                    resp = s.get(item["parents"][0]["url"])
                    if resp.status_code == 200 and len(resp.json())>0:      
                        NewItem = {key:resp.json()[key] for key in CommitProperties}

                        if NewItem not in CommitList:
                            print("Successful")
                            resultlist.append(NewItem)
                        else:
                            print("Already in the list")
                            print(item["html_url"])
                        
                        sleep(1)
                        if in_q is not None:
                            in_q.put((count, len(CommitList)))
                    
                            
                except :
                    print("Error")        
        else:
            print("Complicated")
            with requests.Session() as s:
                s.headers.update(headers)
                for parent in item["parents"]:
                    try:                    
                        resp = s.get(parent["url"])
                        if resp.status_code == 200 and len(resp.json())>0:   
                            NewItem = {key:resp.json()[key] for key in CommitProperties}

                            if NewItem not in CommitList:
                                print("Successful")
                                resultlist.append(NewItem)
                            else:
                                print("Already in the list")
                                print(item["html_url"])
                        
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
    
    for item in CommitList:  
        cond = False
        try:
            Tree = GetTree(item["commit"]["tree"]["url"])

            if type(Tree) is dict and Tree is not {}:
                try:
                    for file in Tree["tree"]:
                        if file["path"]=="pom.xml":
                            #if the commit contains a pom.xml file, then we need it
                            resultlist.append(item)                            
                            cond = True
                            break
                except :
                    print("other error")
            print("lucky find!" if cond else "Missing pom.xml")
        except :
            print("Wrong Tree")
    return resultlist


def WriteCommitsToFile(resultlist, file_path, in_q = None):
    """Writes a Commitlist to a file"""
    count = 1
    with open(file_path+'/QueryResults.txt', 'w') as output_file:
        output_file.write(str(len(resultlist))+"\n")
        for item in resultlist:
            html = item["html_url"]
            sha = item["sha"]
            output_file.write(html[:-(len(sha)+len("/commit/"))]+"\n")
            output_file.write(sha+"\n")

            if in_q is not None:
                in_q.put((count, len(resultlist)))
            count = count+1
    print("Succesful writing")

def CollectData():
    resultlist = []
    mylist = GetRepoList()
    count = 0
    for item in mylist:
        resultlist.append(FilterCommits(GetCommitList(item))) 
        count = count+1
        print("Collecting Commits: "+str(count)+"/"+str(len(mylist)))

    #merging the lists
    resultlist = list(itertools.chain.from_iterable(resultlist))
   
    resultlist = AddParents(resultlist)

    print("Query is completed writing results to a file")
    WriteCommitsToFile(resultlist, "")
    print("Writing was succesful")
   


def DownloadDatabase(input_path="C:/Users/fazon/source/repos/Maven-Github_Database/GithubQuery/GithubQuery", output_path = "E:/Repo", in_q=None):
    """Downlaod the commits from input_path to output_path"""
    
    input_path = str(input_path)
    output_path = str(output_path)
    with open(input_path+"/QueryResults.txt") as fp:
        maxprogress=int(fp.readline()[:-1])
        count =1
        html = fp.readline()
        sha = fp.readline()
        
        os.system(output_path.split(":")[0]+":")#needed to handle both / and \  
        while html:
            #removing the \n from the end
            html=html[:-1]
            sha=sha[:-1]
            os.chdir(output_path)

            #downloading the correct version
            os.system(f"cd {output_path}")
            os.system(f"git clone -n {html} {count}")
            os.chdir(f"{output_path}/{count}")
            os.system(f"git checkout {sha}")
            os.chdir(output_path)
            if in_q is not None:
                in_q.put((count, maxprogress))
            count= count+1
            html = fp.readline()
            sha = fp.readline()
            print(count)
            


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
    """
    Handles the gathering of the repositories while ensuring that the window won't freeze
    input:  window:     The main window
            values:     event values, contains the user input
            phase:      contains information about the role of this function in the total workflow 
            
    """
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
            event, _ = window.read(0.1)           
            if event is None:
                #Stopping threads in case of exit is pressed
                print("Terminating threads")
                executor._threads.clear()
                concurrent.futures.thread._threads_queues.clear()
                sys.exit()
            if (-1,-1) != progress:
                window.Finalize()
                window['lbl_Progbar1'].update(("Getting Repositories, progress: "+str(progress[0])+"/"+str(progress[1])))
                
                window.Finalize()
                window['Progbar1'].update_bar(progress[0], progress[1])
                
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


def Gui_GetCommits(window, values, RepoList, file_path):
    """
    Handles the gathering of the commits while ensuring that the window won't freeze
    input:  window:     The main window
            values:     event values, contains the user input
            RepoList:   List of the collected Repositories
            file_path:  path to the outputfile
    """

    #clears previous results
    CommitList=[]
    
    count = 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

        
        for item in RepoList:     
            window.Finalize()
            window['lbl_Progbar2'].update(("Phase: "+str(2)+"/"+str(4)+" Getting Commits"))
            window['Progbar2'].update_bar(2, 4)
            window['lbl_Progbar1'].update("Starting the query, please stand by")

            #Getting Commits
            future = executor.submit(GetCommitList,item, values)
            while not future.done():
                event, _ = window.read(0.1)           
                if event is None:
                    #Stopping threads in case of exit is pressed
                    print("Terminating threads")
                    executor._threads.clear()
                    concurrent.futures.thread._threads_queues.clear()
                    sys.exit()
                window.Finalize()
                window['lbl_Progbar1'].update(("Getting Commits, progress: "+str(count)+"/"+str(len(RepoList))))
                window['Progbar1'].update_bar(count, len(RepoList))    
                
            result=future.result()
            if type(result) is not list:
                window.Finalize()
                window['lbl_Progbar1'].update(result)
                break

            #Filtering the Commits
            if values["ChBox_SearchPom"] or values["ChBox_DeafultParams"]:  
                future2 = executor.submit(FilterCommits,result, values)
                while not future2.done():
                    event, _ = window.read(0.1)           
                    if event is None:
                        #Stopping threads in case of exit is pressed
                        print("Terminating threads")
                        executor._threads.clear()
                        concurrent.futures.thread._threads_queues.clear()
                        sys.exit()
                    window.Finalize()
                    window['lbl_Progbar1'].update(("Filtering Commits, progress: "+str(count)+"/"+str(len(RepoList))))
                    window['Progbar1'].update_bar(count+1,  len(RepoList))      
                result = future2.result()
            count=count+1
            CommitList.append(result)
        CommitList = list(itertools.chain.from_iterable(CommitList))

        #Adding Parents
        if values["ChBox_AddParents"] or values["ChBox_DeafultParams"]:                
            q = Queue()
            progress = (0, 0)
            window.Finalize()
            window['lbl_Progbar2'].update(("Phase: "+str(3)+"/"+str(4)+" Adding Parents"))
            window['Progbar2'].update_bar(3, 4)
            
            future3 = executor.submit(AddParents,CommitList, q)
            while not future3.done():
                event, _ = window.read(0.1)           
                if event is None:
                    #Stopping threads in case of exit is pressed
                    print("Terminating threads")
                    executor._threads.clear()
                    concurrent.futures.thread._threads_queues.clear()
                    sys.exit()
                if not q.empty():
                    progress = q.get()
                window.Finalize()
                window['lbl_Progbar1'].update(("Adding Parents, progress: "+str(progress[0])+"/"+str(progress[1])))
                window['Progbar1'].update_bar(progress[0],  progress[1])
                    
            CommitList = future3.result()
            window.Finalize()
        
        #Writing to file
        q = Queue()
        progress = (0, 0)
        window.Finalize()
        window['lbl_Progbar2'].update(("Phase: "+str(4)+"/"+str(4)+" Writing results to File"))
        window['Progbar2'].update_bar(4, 4)
        future4 = executor.submit(WriteCommitsToFile,CommitList,file_path, q)
        while not future4.done():
            if not q.empty():
                event, _ = window.read(0.1)           
                if event is None:
                    #Stopping threads in case of exit is pressed
                    print("Terminating threads")
                    executor._threads.clear()
                    concurrent.futures.thread._threads_queues.clear()
                    sys.exit()
                progress = q.get()
                window.Finalize()
                window['lbl_Progbar1'].update(("Writing results to File, progress: "+str(progress[0])+"/"+str(progress[1])))
                window['Progbar1'].update_bar(progress[0],  progress[1])
        window['Progbar1'].update_bar(progress[1],  progress[1])


        window['lbl_Progbar1'].update(("Writing results to File, progress: "+str(progress[1])+"/"+str(progress[1])))
        window['lbl_Progbar2'].update(("Data collection is completed"))

    sg.SystemTray.notify('Query Completed', 'The application succesfully collected the projects')
    return CommitList
    
def Gui_DownloadCommits(window, values,file_path):
    q = Queue()
    progress = (0, 0)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future5 = executor.submit(DownloadDatabase,file_path,file_path, q)
        while not future5.done():
            event, _ = window.read(0.1)
            if event is None:
                    #Stopping threads in case of exit is pressed
                    print("Terminating threads")
                    executor._threads.clear()
                    concurrent.futures.thread._threads_queues.clear()
                    sys.exit()
            if not q.empty():
                progress = q.get()
            window.Finalize()
            window['lbl_Progbar1'].update(("Downloading the projects, progress: "+str(progress[0])+"/"+str(progress[1])))
            window['Progbar1'].update_bar(progress[0],progress[1])
    sg.SystemTray.notify('Download Completed', 'The application succesfully downloaded the projects')

def Gui_MainWindow():
    sg.theme('Dark Blue 13')
    
    #file_path = 'C:\\Users\\fazon\\source\\repos\\Maven-Github_Database\\GithubQuery'
    file_path = pathlib.Path(__file__).parent.absolute()
 # Column layout      
    col_btn = [[sg.Button('Get Repositoires',key='btn_getrepos', size = (20, 3), font=(15))],      
            [sg.Button('Get Commits',key='btn_getcommits', size = (20, 3), font=(15))],      
            [sg.Button('Preview Projects',key='btn_viewprojects', size = (20, 3), font=(15))],
            [sg.Button('Preview Commits',key='btn_viewcommits', size = (20, 3), font=(15))],
            [sg.Button('Download Database',key='btn_Download', size = (20, 3), font=(15))]]      

    col_chbox =  [[sg.Text('Search Parameters:')],
            [sg.Checkbox('Use Default parameters', size=(20, 1),  key='ChBox_DeafultParams', default=True)],
            [sg.Checkbox('Add Parents', size=(20, 1), key='ChBox_AddParents')],      
            [sg.Checkbox('Search pom.xml', size=(20, 1), key='ChBox_SearchPom')],        
            [sg.Checkbox('Limit Repository Number', size=(20, 1), key='ChBox_LimitRepos')],
            [sg.Checkbox('Limits Commit Number', size=(20, 1), key='ChBox_LimitCommits')]]      

    col_params =  [[sg.Text('Query parameters:')],
                  [sg.In(default_text='https://repo1.maven.org/+in:readme' ,key='txtbox_queryparam', size=(80, 1))],
                  [sg.Text('Commit message filter:')],
                  [sg.In(default_text='bug, fix', size=(80, 1),key='txtbox_commitmessage')],
                  [sg.Text('Oauth2Token:')],
                  [sg.In(default_text=MyOauth2Token, size=(80, 1),key='txtbox_oauth2token')]]


    # Bottom
    layout = [[sg.Column(col_btn),sg.Column(col_chbox), sg.Column(col_params)],
              [sg.Button('Choose Location',key='btn_location', size = (20, 3)), sg.Text(file_path, key="lbl_location", size = (80,1)), sg.Button('Start', key='btn_Start', size = (25, 4), pad=((6, 10), 30), font=(15))],
              [sg.Text('', key="lbl_Progbar1",size=(100,1), auto_size_text=True)],
              [sg.ProgressBar(10, orientation='h', size=(96, 20), key='Progbar1')],
              [sg.Text('', key="lbl_Progbar2",size=(100,1), auto_size_text=True)],
              [sg.ProgressBar(3000, orientation='h', size=(96, 20), key='Progbar2')]]

    # create the Window
    window = sg.Window('Database Builder', layout)

    
    RepoList = None
    CommitList = None
    exit_event = mp.Event()
    while True:
   
        event, values = window.read(timeout=0)
        if event != '__TIMEOUT__':
            print(values)
            if event == 'Cancel' or event is None:                
                print("ineteresting")
                break    
            elif event == 'btn_getrepos':
                phase=(1, 1)
                RepoList=Gui_GetRepositories(window, values, phase)

            elif event == 'btn_getcommits':
                if RepoList != None:
                    print(RepoList)
                else:
                    phase=(1, 4)
                    RepoList=Gui_GetRepositories(window, values, phase)

                if RepoList != None:    
                    CommitList=Gui_GetCommits(window, values, RepoList, file_path)     
                print("btn_getcommits")
            elif event == 'btn_viewprojects':
                print("btn_viewprojects")
                if RepoList is not None and len(RepoList)>0:
                    window.Hide()
                    Gui_CreatePreview(RepoList, DisplayableRepoProperties, False)
                    window.UnHide()
            elif event == 'btn_viewcommits':
                print("btn_viewcommits")
                if CommitList is not None and len(CommitList)>0:
                    window.Hide()
                    Gui_CreatePreview(CommitList, DisplayableCommitProperties, True)
                    window.UnHide()
                    
            elif event == 'btn_Download':
                Gui_DownloadCommits(window, values, file_path)                
                    
            elif event == 'btn_location':
                
                new_file_path = filedialog.askdirectory()
                if new_file_path != "":
                    file_path = new_file_path
                    window["lbl_location"].update(file_path)
                print(file_path)
                print("btn_location")
            elif event == 'btn_Start':
                phase = (1, 4)
                RepoList=Gui_GetRepositories(window, values, phase)
                CommitList=Gui_GetCommits(window, values, RepoList, file_path)
                Gui_DownloadCommits(window, values, file_path)  
       
    sys.exit()
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
    """
    Window for browsing the query results
    input:  DictList: list of dictionaries
            Properties: which keys should the program show
                Note: can't show nested properties
            CommitMode: if true, then shows the commit messages first line
                        else it shows only the wanted properties
    """
    sg.theme('Dark Blue 13')
    name=""
    if CommitMode:
        name = "Commits"
    else:
        name = "Projects"

    # ------ Prepare the data for the table ------
   
    data = MakeTableData(Properties, DictList, CommitMode)    
    headings = Properties if not CommitMode else ["Name", "Message"] +Properties
       
   

    # ------ Window Layout ------
    layout = [[sg.Table(values=data[0:][:], headings=headings, max_col_width=25,
                        # background_color='light blue',
                        auto_size_columns=True,
                        display_row_numbers=True,
                        justification='left',
                        num_rows=20,
                        # alternating_row_color='lightyellow',
                        key='-TABLE-',
                        tooltip='List of the Repositories')],
              [sg.Button('Copy Url'),sg.Button('Copy Html Url'), sg.Button('Back')],
              [sg.Text('Copy Url = Copies the API link')],
              [sg.Text('Copy Html Url =  Copies the HTML link')]]

    # ------ Create Window ------
    window = sg.Window('Preview '+name, layout)

    # ------ Event Loop ------
    while True:
        event, values = window.read()
        print(event, values)
        if event is None:
            break
        if event == 'Copy Html Url':
            print("enter")
            if len(values['-TABLE-'])==1:
                print(values['-TABLE-'][0])
                url=""
                if not CommitMode:
                    url = window['-TABLE-'].Values[values['-TABLE-'][0]][len(Properties)-2]
                else:
                    url = window['-TABLE-'].Values[values['-TABLE-'][0]][len(Properties)]
                print(url)
                print("asd")
                copy2clip(url)
        if event == 'Copy Url':
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
Gui_MainWindow()
#hide  the console
#ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

#ProjectPreview
#RepoList=GetRepoList()