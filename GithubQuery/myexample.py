with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(GetRepoList, q, values)
        progress = (-1, -1)
        while not future.done():
            event, values = window.read(0.1)
            print(event, values)
            if event is None:
                print("Jello")
                executor._threads.clear()#eldob minden szálat
                concurrent.futures.thread._threads_queues.clear()#ez is
                sys.exit()#kilép a főorigramból
            if (-1,-1) != progress:
                window.Finalize()
                window['lbl_Progbar1'].update(("Getting Repositories, progress: "+str(progress[0])+"/"+str(progress[1])))
                
                window.Finalize()
                window['Progbar1'].update_bar(progress[0], progress[1])