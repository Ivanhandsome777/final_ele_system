import pandas as pd
import datetime
import time
import threading



# def merge_history():
#     #将所有日期的数据合并，读取到内存
#     global df_merged
#     df_merged=pd.DataFrame({})
#     pass
#     # return df_mergedcsv

# def recovery(df_mergecsv,a,b): #通过a,b两个参数的传入，达成拆分任务的目的
#     print(f'proceeding with task {a}-{b}')
#     query_tree=[]
#     return query_tree

# def csv_job(filename,a,b):
#     global trees,df_merged
#     tree=recovery(df_merged,a,b)
#     trees.append(tree)
#     recovery(df_merged,a,b)

# def batchJobs():
#     today = datetime.datetime.today()
#     date_str = today.strftime("%Y.%m.%d")  # 例如: "2025.09.20"
#     filename_date = date_str.replace(".", "_")  # 转换为"2025_09_20"
#     filename = f"{filename_date}.csv"

#     global df_ele #现在df_ele有了数据（因为前一流程）
#     df_ele.to_csv(filename, index=False)

#     global trees
#     trees=[]
#     merge_history() #准备好第二个工作的数据

#     threads=[]
#     for a in range(10):
#         for b in range(3):
#             t=threading.Thread(target=csv_job, args=(filename,a,b))
#             threads.append(t)
#             t.start()
#     for each in threads:
#         each.join()


def recovery(a,b): #通过a,b两个参数的传入，达成拆分任务的目的
    print(f'proceeding with task {a}-{b}')
    # query_tree=[]
    # return query_tree

def csv_job(a,b):
    recovery(a,b)
    time.sleep(b*0.1)
    print(f"job {a}-{b} completed")



def batchJobs():
    today = datetime.datetime.today()
    date_str = today.strftime("%Y.%m.%d")  # 例如: "2025.09.20"
    filename_date = date_str.replace(".", "_")  # 转换为"2025_09_20"
    filename = f"{filename_date}.csv"

    global df_ele #现在df_ele有了数据（因为前一流程）
    df_ele.to_csv(filename, index=False)

    threads=[]
    for a in range(10):
        for b in range(3):
            t=threading.Thread(target=csv_job, args=(a,b))
            threads.append(t)
            t.start()
    for each in threads:
        each.join()