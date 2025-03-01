import pandas as pd
import datetime
import time
import threading


def recovery(a,b): # This a pseudo code, since it's still not applicable to incorporate the tree
    print(f'proceeding with task {a}-{b}')
    # query_tree=[]
    # return query_tree

def csv_job(a,b):
    recovery(a,b)
    time.sleep(b*0.1)
    print(f"job {a}-{b} completed")



def batchJobs():
    today = datetime.datetime.today()
    date_str = today.strftime("%Y.%m.%d")  
    filename_date = date_str.replace(".", "_")  
    filename = f"{filename_date}.csv"

    global df_ele 
    df_ele.to_csv(filename, index=False)

    threads=[]
    for a in range(10):
        for b in range(3):
            t=threading.Thread(target=csv_job, args=(a,b))
            threads.append(t)
            t.start()
    for each in threads:
        each.join()