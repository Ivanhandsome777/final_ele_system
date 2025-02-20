# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 21:56:20 2025

@author: 30048
"""

# Source: Geeksforgeeks

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for,render_template
import os
import csv
from datetime import datetime, timedelta
# import functions
from functions import calculate_usage,calculate_billing,preprocess_data,export_data
from functions import write_log,init_logger,init_daily_csv
import dash
from dash import dcc, html, Input, Output
from dash import dash_table
import plotly.express as px
from flask import send_file,jsonify
import threading
from jobs import batchJobs

app = Flask(__name__)
df = pd.read_csv('data.csv')
df = preprocess_data(df)
global_start_date = None
global_end_date = None

global asd #accidental shutdown
global admins,users,log_lock,df_ele
admins = {} # {email address, password}
users = {}  # { identifier: {address, region, sub_region, postcode, apartment_type} }
log_lock = threading.Lock()
df_ele = pd.DataFrame(columns=['identifier', 'usage', 'timestamp'])  # Initialize DataFrame


init_logger() # 启动后台线程处理数据：这里会先检查log如果存在，说明之前意外掉线
init_daily_csv()


# 初始化 Dash 应用
dashapp = dash.Dash(__name__, server=app, url_base_pathname="/government/query/analysis/")



meter_readings = [
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 19, 0, 30), "reading_kwh": 144.5},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 18, 22, 0), "reading_kwh": 140},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 1, 18, 22, 30), "reading_kwh": 30},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 2, 12, 22, 30), "reading_kwh": 50},
    {"meter_id": "524-935-527", "timestamp": datetime(2025, 1, 1, 22, 30), "reading_kwh": 10},
]

LOG_FILE = 'meter_logs.txt'

# **Load CSV Data When Flask Starts**

def load_data():
    global admins, users
    # load data from admins.csv
    with open("admins.csv", "r") as file:
        reader = csv.DictReader(file)
        admins = {row["email"]: {"password": row["password"]} for row in reader}
    # load data from users.csv
    with open("users.csv", "r") as file:
        reader = csv.DictReader(file)
        users = {row["identifier"]: row for row in reader}

# save updated users profile to CSV when Flask is shut down
def save_data():
    with open("users.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["identifier", "address", "region", "sub_region", "postcode", "apartment_type"])
        writer.writeheader()
        for identifier, data in users.items():
            data_with_id = {"identifier": identifier, **data}  # Include identifier in the dictionary
            writer.writerow(data_with_id)

# initial main page of the website, and directly link to the /company/login page for company_side requests
@app.route("/", methods=["GET"])
def mainsite():
    if acceptAPI:
        return(render_template('home.html'))
    else:
        return(render_template('api_shutdown.html'))
        
@app.route("/User/query",methods=["GET","POST"])
def user_query():
    if request.method == 'POST':
        meter_id = request.form.get('meter_id')
        time_range = request.form.get('time_range')
        
        if not meter_id or not time_range:
            return render_template('user_query.html', error="please input all parameters needed")
            
        # 记录日志
        with open(LOG_FILE, 'a') as f:
            f.write(f"{datetime.now()}: 查询请求 - 电表ID: {meter_id}, 时间范围: {time_range}\n")
            
        return redirect(url_for('result', 
                             meter_id=meter_id,
                             time_range=time_range))
    
    return render_template('user_query.html')

@app.route('/User/query/result')
def result():
    meter_id = request.args.get('meter_id')
    time_range = request.args.get('time_range')
    
    usage = calculate_usage(meter_id, time_range)
    billing = calculate_billing(meter_id)
    
    if usage is None or billing is None:
        return render_template('user_query_result.html',
                             error="can not find data or insufficient data",
                             meter_id=meter_id)
    
    return render_template('user_query_result.html',
                         meter_id=meter_id,
                         time_range=time_range,
                         usage=usage,
                         billing=billing)


dashapp.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # 新增
    html.H1("Eletricity Usage Visualized Analysis"),
    
    # 时间选择
    html.Label("Chosen Time Range:"),
    dcc.DatePickerRange(
        id='date-picker',
        start_date=df['timestamp'].min(),
        end_date=df['timestamp'].max(),
        display_format='YYYY-MM-DD'
    ),
    
    html.Br(),
    
    # 折线图选择
    dcc.RadioItems(
        id='line-chart-option',
        options=[
            {'label': 'By year', 'value': 'year'},
            {'label': 'By quarter', 'value': 'quarter'}
        ],
        value='year',
        inline=True
    ),
    dcc.Graph(id='line-chart'),

    html.Br(),

    # 饼图选择
    dcc.RadioItems(
        id='pie-chart-option',
        options=[
            {'label': 'By Dwelling Type', 'value': 'dwelling_type'},
            {'label': 'By Region', 'value': 'Region'}
        ],
        value='dwelling_type',
        inline=True
    ),
    dcc.Graph(id='pie-chart'),

    html.Br(),

    # 导出数据按钮
    html.Button("Export data", id="export-btn", n_clicks=0),
    html.A("Download CSV", id="download-link", href="", target="_blank", style={"display": "none"})
])
@dashapp.callback(
    [Output('date-picker', 'start_date'),
     Output('date-picker', 'end_date')],
    [Input('url', 'search')]
)
def update_date_range(search):
    """ 从 URL 参数解析时间范围 """
    from urllib.parse import parse_qs
    params = parse_qs(search.lstrip('?'))
    global global_start_date, global_end_date
    global_start_date = params.get('start', [None])[0]
    global_end_date = params.get('end', [None])[0]
    return global_start_date, global_end_date

@dashapp.callback(
    Output('line-chart', 'figure'),
    [Input('line-chart-option', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_line_chart(option, start_date, end_date):
    """ 修正季度显示问题 """
    filtered_df = df[
        (df['timestamp'] >= pd.to_datetime(start_date)) & 
        (df['timestamp'] <= pd.to_datetime(end_date))
    ]
    
    if option == 'year':
        df_grouped = filtered_df.groupby('year')['recent_usage'].sum().reset_index()
        fig = px.line(df_grouped, x='year', y='recent_usage', title="Yearly Electricity Usage Fluctuation")
        fig.update_xaxes(type='category')  # 强制显示为分类数据
    else:
        # 生成友好季度格式（YYYY-Q1）
        filtered_df['quarter'] = filtered_df['timestamp'].dt.to_period("Q").dt.strftime('%Y-Q%q')
        df_grouped = filtered_df.groupby('quarter')['recent_usage'].sum().reset_index()
        fig = px.line(df_grouped, x='quarter', y='recent_usage', title="Quarterly Electricity Usage Fluctuation")
        fig.update_xaxes(type='category')  # 强制显示为分类数据
    
    return fig

@dashapp.callback(
    Output('pie-chart', 'figure'),
    [Input('pie-chart-option', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_pie_chart(option, start_date, end_date):
    """ 带时间过滤的饼图 """
    filtered_df = df[
        (df['timestamp'] >= pd.to_datetime(start_date)) & 
        (df['timestamp'] <= pd.to_datetime(end_date))
    ]
    
    if option == 'dwelling_type':
        df_grouped = filtered_df.groupby('dwelling_type')['recent_usage'].sum().reset_index()
        title = "Electricity Usage Distribution by Dwelling Types"
    else:
        df_grouped = filtered_df.groupby('Region')['recent_usage'].sum().reset_index()
        title = "Electricity Usage Distribution by Regions"
    
    fig = px.pie(df_grouped, names=option, values='recent_usage', title=title,hole=0)
    fig.update_layout(
    width=600,  # 设置宽度
    height=600,  # 设置高度
    margin=dict(l=20, r=20, t=40, b=20)  # 调整边距
)
    return fig

@dashapp.callback(
    Output("download-link", "href"),
    Output("download-link", "style"),
    [Input("export-btn", "n_clicks")],
    [dash.dependencies.State('date-picker', 'start_date'),
     dash.dependencies.State('date-picker', 'end_date')]
)
def export_csv(n_clicks, start_date, end_date):
    if n_clicks > 0:
        file_name = export_data(df, start_date, end_date)
        return f"/download/{file_name}", {"display": "block"}
    return "", {"display": "none"}

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route("/government/query/", methods=["GET", "POST"])
def government_query():
    if request.method == "POST":
        start_date = request.form.get("start")
        end_date = request.form.get("end")
        # 重定向到 Dash 页面并携带参数
        return redirect(f"/government/query/analysis/?start={start_date}&end={end_date}")
    return render_template("government_query.html")


@app.route("/company/login", methods=["GET", "POST"])
def company_login():
    if request.method == "POST":
        email = request.form.get("email")  # Use .get() to prevent KeyError
        password = request.form.get("password")

        # raise error if email is not found in admin reference table
        if email in admins and admins[email].get("password") == password:
            return redirect(url_for("company_main"))

        return render_template("company_login.html", message="Invalid credentials. Try again.")

    return render_template("company_login.html")


# main page after login, i.e. the dash board for company employee
@app.route("/company/main", methods=["GET", "POST"])
def company_main():
    return render_template('company_main.html')

# company register
@app.route("/company/register", methods=["GET", "POST"])
def register_user():
    if request.method == "POST":
        identifier = request.form["identifier"]
        address = request.form["address"]
        region = request.form["region"]
        sub_region = request.form["sub_region"]
        postcode = request.form["postcode"]
        apartment_type = request.form["apartment_type"]

        # raise message if identifier already exist
        if identifier in users:
            return render_template("company_register.html", message="Identifier already exists! Try again.")

        # base on input message, create new user profile to memory
        users[identifier] = {
            "address": address,
            "region": region,
            "sub_region": sub_region,
            "postcode": postcode,
            "apartment_type": apartment_type
        }
        return render_template("company_register.html", message=f"New user {identifier} registered successfully!", success=True)
    # post the input data to the html webpage
    return render_template("company_register.html")

# modify currently existed users' profile
@app.route("/company/modify", methods=["GET", "POST"])
def modify_user():
    if request.method == "POST":
        identifier = request.form["identifier"]

        # raise error to notify that unavailable identifier input
        if identifier not in users:
            return render_template("company_modity.html", message = 'User not found! Try again')

        # update the user profile in system's memory and wait to be written to csv back-up after system shutting down
        users[identifier] = {
            "address": request.form["address"],
            "region": request.form["region"],
            "sub_region": request.form["sub_region"],
            "postcode": request.form["postcode"],
            "apartment_type": request.form["apartment_type"]
        }
        return render_template("company_modify.html", message = f"User {identifier} modified successfully!", success = True)

    return render_template("company_modify.html")

# deactivate a user's identifier
@app.route("/company/deactivate", methods=["GET", "POST"])
def deactivate_user():
    if request.method == "POST":
        identifier = request.form.get("identifier")

        # raise message to notify: user not found
        if identifier not in users:
            return render_template("company_deactivate.html", message = "User not found! Please try again")
        # if found user identifier, delete it from the memory table and update to csv system file after shutting
        del users[identifier]
        return render_template('company_deactivate.html', message = f"user {identifier} deleted successfully, wait for system udpate", success = True)

    return render_template('company_deactivate.html')


@app.route("/company/meter", methods=["GET", "POST"])
def meter_uploading():
    if request.method == "POST":
        identifier = request.form["identifier"]
        usage = request.form["usage"]

        if identifier in users:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

            # Update DataFrame (Ensure global usage)
            global df_ele
            new_row = {'identifier': identifier, 'usage': usage, 'timestamp': timestamp}
            new_df = pd.DataFrame([new_row])
            df_ele = pd.concat([df_ele, new_df], ignore_index=True)
            print(df_ele)

            # Append to log file
            with log_lock:
                try:
                    write_log(identifier, timestamp, usage)
                    return redirect(url_for("meter_uploaded", identifier=identifier, timestamp=timestamp, usage=usage))
                except Exception as e:
                    return jsonify({'message': 'Data uploading failed.'})

        return render_template("meter_upload.html", error="Invalid credentials. Try again.")

    return render_template("meter_upload.html", error=None)

@app.route("/meter_uploaded")
def meter_uploaded():
    identifier = request.args.get("identifier")
    timestamp = request.args.get("timestamp")
    usage = request.args.get("usage")
    return render_template("upload_success.html", identifier=identifier, timestamp=timestamp, usage=usage)



@app.route('/stopServer', methods = ['GET','POST'])
def stop_server():
    global acceptAPI
    acceptAPI = False
    save_data()
    batchJobs()
    acceptAPI = True
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if shutdown:
        shutdown()
    return "<h1>Server is shutting down...</h1>"

   


# quit the whole system (not finished yet)
@app.route("/company/quit")
def quit_app():
    pass

# initiate the app
if __name__ == '__main__':
    load_data() # load admin and users profile before initiating the app
    print(users)
    try:
        app.run(debug=False) # using debug = True will result in anaconda bugs, how to fix it?
    finally:
        save_data() # save changes on the users profile