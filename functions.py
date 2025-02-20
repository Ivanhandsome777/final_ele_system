import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import os

meter_readings = [
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 19, 0, 30), "reading_kwh": 144.5},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 18, 22, 0), "reading_kwh": 140},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 1, 18, 22, 30), "reading_kwh": 30},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 12, 22, 30), "reading_kwh": 50},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 1, 1, 22, 30), "reading_kwh": 10},
]

LOG_FILE = 'meter_logs.txt'

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