import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import os
import random
import threading
from BTree import BTree

meter_readings = [
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 19, 0, 30), "reading_kwh": 144.5},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 18, 22, 0), "reading_kwh": 140},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 1, 18, 22, 30), "reading_kwh": 30},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 12, 22, 30), "reading_kwh": 50},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 1, 1, 22, 30), "reading_kwh": 10},
]

LOG_FILE = 'meter_logs.txt'



def write_log(identifier, timestamp, usage):
    """Appends meter data to log.txt."""
    with open("log.txt", "a") as f:
        f.write(f"{identifier},{timestamp},{usage}\n")


global lock
global users, df_ele
lock = threading.Lock()

# 初始化日志
def init_logger():
    global asd,df_ele
    log_file_path = "log.txt"
    
    # 检查log.txt是否存在或为空
    if not os.path.exists(log_file_path) or os.path.getsize(log_file_path) == 0:
        asd = False
        # 创建空的log.txt文件
        with open(log_file_path, 'w') as f:
            pass
        
        # 创建空的DataFrame
        df_ele = pd.DataFrame(columns=['identifier', 'timestamp', 'usage'])
    else:
        # 读取log.txt文件并加载到DataFrame中
        df_ele = pd.read_csv(log_file_path, names=['identifier', 'timestamp', 'usage'],sep=',')
        asd = True
    return df_ele


def init_daily_csv():
    # 获取当前日期并格式化为指定字符串
    today = datetime.today()
    date_str = today.strftime("%Y.%m.%d")  # 例如: "2025.09.20"
    filename_date = date_str.replace(".", "_")  # 转换为"2025_09_20"
    filename = f"{filename_date}.csv"
    
    # 检查文件是否存在
    if not os.path.exists(filename):
        # 使用全局变量df_ele保存CSV
        global df_ele
        df_ele.to_csv(filename, index=False)




def calculate_usage(meter_id, time_range):
    # 获取目标电表的所有读数并按时间排序
    readings = sorted(
        [r for r in meter_readings if r['meter_id'] == meter_id],
        key=lambda x: x['timestamp']
    )
    if not readings:
        return None

    # 确定时间范围边界
    now = datetime.now()
    if time_range == 'last_half_hour':
        start_time = now - timedelta(minutes=30)
        end_time = now
    elif time_range == 'today':
        start_time = datetime(now.year, now.month, now.day)
        end_time = now
    elif time_range == 'week':
        start_time = now - timedelta(days=now.weekday())
        end_time = now
    elif time_range == 'month':
        start_time = datetime(now.year, now.month, 1)
        end_time = now
    elif time_range == 'last_month':
        end_time = (now.replace(day=1) - timedelta(days=1))
        start_time = end_time.replace(day=1)
    else:
        return None

    # 找到最接近时间范围边界的读数
    def find_closest(readings, target, mode):
        """
        mode: 'floor' (<= target) or 'ceil' (>= target)
        """
        candidates = []
        for r in readings:
            if mode == 'floor' and r['timestamp'] <= target:
                candidates.append(r)
            elif mode == 'ceil' and r['timestamp'] >= target:
                candidates.append(r)
        
        return max(candidates, key=lambda x: x['timestamp']) if candidates and mode == 'floor' \
               else min(candidates, key=lambda x: x['timestamp']) if candidates and mode == 'ceil' \
               else None

    # 获取边界读数
    start_reading = find_closest(readings, start_time, 'ceil')  # 第一个>=start_time的读数
    end_reading = find_closest(readings, end_time, 'floor')     # 最后一个<=end_time的读数

    if not start_reading or not end_reading:
        return None

    # 确保时间顺序有效
    if start_reading['timestamp'] > end_reading['timestamp']:
        return None

    return round(end_reading['reading_kwh'] - start_reading['reading_kwh'], 2)

def calculate_billing(meter_id):
    # 获取上月时间范围
    today = datetime.now()
    last_month_end = (today.replace(day=1) - timedelta(days=1))
    last_month_start = last_month_end.replace(day=1)
    
    # 获取相关读数
    readings = sorted(
        [r for r in meter_readings if r['meter_id'] == meter_id],
        key=lambda x: x['timestamp']
    )
    
    # 查找边界读数
    start_reading = next((r for r in readings if r['timestamp'] >= last_month_start), None)
    end_reading = next((r for r in reversed(readings) if r['timestamp'] <= last_month_end), None)
    
    if not start_reading or not end_reading:
        return None
    
    return round(end_reading['reading_kwh'] - start_reading['reading_kwh'], 2)




def preprocess_data(df):
    """
    计算每个电表的最近一次用电量
    """
    df['timestamp'] = pd.to_datetime(df[['year', 'month', 'day', 'time']].astype(str).agg(' '.join, axis=1))
    df = df.sort_values(by=['Identifier', 'timestamp'])

    df['prev_reading'] = df.groupby('Identifier')['kwh_per_acc'].shift(1)
    df['recent_usage'] = df['kwh_per_acc'] - df['prev_reading']
    df['recent_usage'] = df['recent_usage'].fillna(0)
    df = df[df['recent_usage'] >= 0]

    return df

def export_data(df, start_date, end_date, file_name='exported_data.csv'):
    """ 增加时间过滤 """
    filtered_df = df[
        (df['timestamp'] >= pd.to_datetime(start_date)) & 
        (df['timestamp'] <= pd.to_datetime(end_date))
    ]
    filtered_df.to_csv(file_name, index=False)
    return file_name


# generate random meter IDs
def generate_meter_ids(num_meters):
    return {f"531-{random.randint(100, 999)}-{random.randint(100, 999)}" for _ in range(num_meters)}

# meter_ids = generate_meter_ids(10)
# print(meter_ids)

# generate meter readings
def generate_readings(meter_ids):
    readings_list = []

    # set the starting and ending time period to be yesterday's and today's 1200am
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    start_of_today = datetime(now.year, now.month, now.day, 0, 0, 0)

    for meter_id in meter_ids:
        # randomizing starting timestamp between 1200am and 01000am 
        start_time = datetime(yesterday.year, yesterday.month, yesterday.day, 0, random.randint(0, 59), random.randint(0, 59))

        # initialize the first meter reading between 100 and 500
        initial_reading = random.uniform(100, 500)
        readings_list.append({"id": meter_id, "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"), "electricity": round(initial_reading, 2)})

        # generate readings every 30 minutes for the whole day until today's 1200am
        current_time = start_time + timedelta(minutes=30)
        last_reading = initial_reading

        while current_time < start_of_today:
            new_reading = last_reading + random.uniform(1, 10)  # Increment previous reading
            readings_list.append({"id": meter_id, "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"), "electricity": round(new_reading, 2)})
            last_reading = new_reading
            current_time += timedelta(minutes=30)

    # convert to df and sort the order
    df = pd.DataFrame(readings_list).sort_values(by=["timestamp"], ascending=False).reset_index(drop=True)
    
    return df


def generate_readings_designate_date(meter_ids, date):
    readings_list = []

    target_date = datetime.strptime(date, "%Y-%m-%d")
    previous_day = target_date - timedelta(days=1)
    start_of_target_day = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)

    for meter_id in meter_ids:
        # 随机选择起始时间（介于 00:00 AM - 01:00 AM）
        start_time = datetime(previous_day.year, previous_day.month, previous_day.day, 0, random.randint(0, 59), random.randint(0, 59))

        # 初始化初始电表读数（100-500 之间）
        initial_reading = random.uniform(100, 500)
        readings_list.append({
            "id": meter_id,
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "electricity": round(initial_reading, 2)
        })

        # 生成每 30 分钟的读数，直到目标日期的 00:00 AM
        current_time = start_time + timedelta(minutes=30)
        last_reading = initial_reading

        while current_time < start_of_target_day:
            new_reading = last_reading + random.uniform(1, 10)  # 在前一个读数基础上递增
            readings_list.append({
                "id": meter_id,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "electricity": round(new_reading, 2)
            })
            last_reading = new_reading
            current_time += timedelta(minutes=30)

    # 转换为 DataFrame，并按照时间倒序排序
    df = pd.DataFrame(readings_list).sort_values(by=["timestamp"], ascending=False).reset_index(drop=True)
    
    return df

# meter_ids = ["meter_1", "meter_2", "meter_3"]
# date = "2024-02-15"  

# df = generate_readings_designate_date(meter_ids, date)
# print(df.head()) 


def transform_df(df,column_name):
    if column_name == "index":
        turple_list = [(x,y) for x,y in zip(df["index"].to_list(),df["kwh_per_acc"].to_list())]
    else:
        turple_list = [(x,y) for x,y in zip(df[column_name].to_list(),df["index"].to_list())]
        
    return turple_list


def transform2Tree(df,column_list):
    tree_dict = {}
    for i in column_list:
        tuple_unit = transform_df(df,i)
        tree = BTree(3)
        for key,value in tuple_unit:
            tree.insert(key,value)
        tree_dict[i] = tree
    return tree_dict
# column_list = ["index","Identifier","dwelling_type","Region","day","time"]
# tree_dict = transform2Tree(column_list)


def ele_query(tree_dict,Identifier=None,dwelling_type=None,Region=None,day=None,time=None):
    """
    "index","Identifier","dwelling_type","Region","day","time"
    """
    dict_parameter = {"Identifier":Identifier,"dwelling_type":dwelling_type,"Region":Region,"day":day,"time":time}
    query_result_list=[]
    activatd_parameter_list = []
    for key,value in dict_parameter.items():
        if value is not None:
            tree_selected = tree_dict[key]
            unit_result = tree_selected.search(value)
            query_result_list.append(unit_result)
            activatd_parameter_list.append((key,value))
        
    query_result_index = list(set(query_result_list[0]).intersection(*query_result_list[1:]))
    ele_result_dict={}
    for num,pair_kk in enumerate(activatd_parameter_list):
        name_key=f"query_info{num}"
        ele_result_dict[name_key] = pair_kk
    index_tree = tree_dict["index"]
    for i in query_result_index:
        ele_result_dict[i] = index_tree.search(i)


    return ele_result_dict


