# SG Group Electricity Meter Usage Upload and Management System

## Brief Function Introduction
![{B572E23B-D795-4E4F-8165-79DAB28A6DB0}](https://github.com/user-attachments/assets/39363649-358e-4b1d-95ee-08fae13039d1)
As shown in the flow chart, the function contains 2 major parts:
* **Meter usage data up load and managemen**t: We used a local users.csv file to manage the registered users. The usage data is stored into log.txt once it is uploaded. At the end of the day, log.txt data(with a corresponding dataframe in the memory) will be flushed into local file MM_DD.csv.
* **Fast-querying, aggregated analysis support and dashboard**: The part we integrate all the historic data in the locals and read it in as a DataFrame. The DataFrame can be transformed to a tree-like data structure for easier querying. The in-memory data structure can support different kind of sorting and filtering query. Ideally, the query result(a DataFrame subset) will then be sent to Dash frontend for analysis need.

## Two Important Logic to Keep in Mind
* **Instant back up**: Every time a reading is read in, usage data is stored in log.txt and appended to in-memory
* **Batch job**: At the end of every day at 12:00AM, we manually sent in "/stopServer" from address to simulate the stopping of API. After this is triggered, batch job will start. The batch job task includes backing up log to csv(named it as MM_DD.csv) and generate query tree in the memory through threading method.

## How to run the code
### Register User and Upload Meter Readings
1. Please run python app.py at the terminal. It is the main code that contains the 23X7 operations. This will initialize the two files(log.txt and MM_DD.csv, mimicing a new day) ![{6C5538CE-9A10-459C-8196-BC75CF3C810D}](https://github.com/user-attachments/assets/0d59b4fa-751e-4db7-9a80-32a29f7b5aa9)
2. Enter this page in the red box and register for user. If you had registerred before, you can not register again.(The user ID will be stored after the program is shutdown. Currently, it is stored in the memory.)![image](https://github.com/user-attachments/assets/f13af2d2-d2c0-42af-b056-70bb5d20ee52) The account is: admin@example.com; and the password is password123.(As stored in admins.csv)
3. After registerring user, you will be able to upload meter readings: enter this page and enter the readings.![image](https://github.com/user-attachments/assets/1ab7e36f-daae-40a8-9f43-0cbb45eec4ed). 
4. Once the reading is uploaded, the data will directly be flushed into log.txt with timestamp.![{EB65869F-31D8-4015-8663-652F90FD2E7D}](https://github.com/user-attachments/assets/c02c14dd-0c77-42b6-9d59-8a06a4022170)![{D9ECF079-1EB1-4F7B-A2D1-9579FB146D40}](https://github.com/user-attachments/assets/e276bbfd-1e86-4d50-93d4-97631c35b0f2)
5. If you don't know how to proceed with manipulation, you can visit this address: https://expert-telegram-469jp4jwqp4c76j9-5000.app.github.dev/

## Independent Functions
### **1. Functions in the functions.py Modules:**
_Logging and Initialization Functions_
* write_log(identifier, timestamp, usage): Appends meter data (identifier, timestamp, and usage) to log.txt. Ensures persistence of meter readings.
* init_logger(): Initializes the logging system by checking if log.txt exists and is non-empty. If empty, creates an empty DataFrame; otherwise, loads data into a DataFrame. Sets a global flag asd to indicate whether data was loaded successfully.
* init_daily_csv(): Creates a daily CSV file named after the current date if it doesn't exist. Saves df_ele (meter readings DataFrame) to this file.

_Meter Reading and Billing Calculation:_
* calculate_usage(meter_id, time_range): Computes electricity consumption within a specified time range (last_half_hour, today, week, month, last_month). Finds the closest meter readings at the start and end of the time range. Returns the difference between start and end readings.
* calculate_billing(meter_id): Calculates electricity consumption for the previous month. Identifies meter readings at the start and end of last month. Computes the total consumption for billing.

_Data Processing and Exporting_
* preprocess_data(df): Converts separate time-related columns into a timestamp column. Sorts data by Identifier and timestamp. Computes recent electricity usage per meter by subtracting the previous reading. Removes invalid (negative) usage records.
* export_data(df, start_date, end_date, file_name='exported_data.csv'): Filters the DataFrame for meter readings within the specified date range. Exports the filtered data to a CSV file.

_Meter Reading Data Generation_
* generate_meter_ids(num_meters): Generates a set of unique random meter IDs in the format "531-XXX-XXX".
* generate_readings(meter_ids): Simulates electricity meter readings for the past day. Starts from a random timestamp and generates readings every 30 minutes. Uses random increments between 1 and 10 kWh per reading.
* generate_readings_designate_date(meter_ids, date): Similar to generate_readings(), but allows the user to specify a target date for readings.

### **2. Functions in the job.py Modules:**


### **3. Other Codes That are Not Applied:**
* **meter_gen.py**:This code generates simulated electricity meter readings for the past six months by creating random meter IDs and assigning incremental electricity consumption values at 30-minute intervals. The generated data is stored in a Pandas DataFrame, saved as a CSV file for further analysis.
*  **tree_index_query_system**: This code aims at the formation of a tree-like data struction, a self-balancing search tree that maintains sorted data and allows for efficient insertions, deletions, and searches. It speeds up queries by keeping keys sorted and minimizing disk accesses (or memory lookups) through hierarchical indexing, enabling **O(log n)** search time compared to **O(n)** in an unsorted list or **O(log n)** in a balanced binary search tree with fewer nodes per level. This code initially aims at serving as on of the "job" within the "batch job" threading processing. However due to time limit, we were unable to incorporate the local historic file to input into the tree-generating algothrithm. Ideally, whenever we run the batch job, we will be able to recreate the tree-structure with the most updated data.

