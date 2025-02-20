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
### Register User
1. Please run python app.py at the terminal. It is the main code that contains the 23X7 operations. This will initialize the ![{6C5538CE-9A10-459C-8196-BC75CF3C810D}](https://github.com/user-attachments/assets/0d59b4fa-751e-4db7-9a80-32a29f7b5aa9)
2. Enter this page in the red box and register for user. (The user ID will be stored after the program is shutdown. Currently, it is stored in the memory.)![image](https://github.com/user-attachments/assets/f13af2d2-d2c0-42af-b056-70bb5d20ee52) The account is: admin@example.com; and the password is password123.(As stored in admins.csv)
3. 

