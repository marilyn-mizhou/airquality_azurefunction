# Real-Time Air Quality Dashboard

Recently, I purchased an air quality monitor as I kept wondering how bad the air quality around my work desk in the living room gets during winter. It rains almost every day in Vancouver, and we tend to keep all the windows closed to keep the cold air out. I was expecting to have some level of carbon dioxide accumulation since our apartment is relatively compact, but oh man... who knew it could be this high! No wonder I occasionally feel light-headed.

The air quality monitor is from AirGradient, and it is fully open-source (https://www.airgradient.com/indoor/). It comes with a pre-built, slightly customizable dashboard and a one-year premium subscription. All the hardware settings and user configurations can be modified through the dashboard as well. There is nothing wrong with using their services. In fact, AirGradient is one of the most ethical companies I can ever imagine. 

As one of the "go-off-the-grid" initiatives in our household, the ultimate goal is to bypass the default AirGradeint cloud, store the collected data in a local database and build a custom real-time dashboard. However, since I was already learning Azure and Power BI, using the air quality data seemed like a perfect practice. Instead of establishing the entire pipeline on a Raspberry Pi, the objective of this intermediate project is to pull data directly from AirGradeint cloud, store in an Azure SQL database and build a dashboard in Power BI. This approach gives me an opportunity to test the workflow and better understand my preferences before fighting real estate for the bridging device in our already tight apartment.

Here is an overview of the data pipeline.
```mermaid
---
config:
  look: handDrawn
  theme: neutral
  layout: elk
---
flowchart LR
    ag_cloud@{shape: cloud, label: "AirGradient \nCloud API"}
    az_func@{shape: processes, label: "Azure \nFunction"}
    az_sql_server@{shape: lin-cyl, label: "Azure SQL \nServer"}
    az_sql_db@{shape: cyl, label: "Azure SQL \nDatabase"}
    bi_dashboard@{shape: tag-doc, label: "Power BI \nDashboard"}
    
    az_func e1@==>|Timer Trigger| ag_cloud
    ag_cloud ==>|Extract Data| az_func
    az_func ==>|Request Access| az_sql_server
    az_sql_server ==>|Store Data| az_sql_db
    bi_dashboard ==>|Request Access| az_sql_server
    az_sql_db ==>|Access Data| az_sql_server

    e1@{animate: true, animation: slow}
```

## Create SQL Server and Database in Azure Portal
1. There are multiple ways to start the process. If "Azure SQL Database" is not in the quick access side bar, search in the search box on the top of the portal and then click "Create".
2. Create or select a Resource Group. A resource group is a container that holds all related resources for one solution (i.e. all Azure services that I will be using to build the dashboard). In this case, I am creating a new group named "AirQuality" and it will be selected throughout the entire project. Enter a name for the database and since I don't have a server yet, I need to create one in the next step.
![alt text](images/sql_setup_1.png)
3. Choose a name and a location for the server. I choose to use both SQL and Microsoft Entra authentication in this case. The server admin login credentials will be used in the function app to access the server and database. Click "OK".
![alt text](images/sql_setup_2.png)
4. Click "Review + create".
![alt text](images/sql_setup_3.png)
5. Click "Create".
![alt text](images/sql_setup_4.png)
6. A SQL server and a SQL database will be ready to use shortly.



## Create Github Repository
I am going to create a github repository to store all function app files.
![alt text](images/github_setup_1.png)




## Initiate Function App in Azure Portal
1. Similar to SQL database, search "function" in the portal and click "Create".
2. Previously, the default plan is Consumption. However, the Consumption plan no longer supports Python, which is the language that I intended to use. Flex Consumption hosting plan is sufficient for my project. In additon to the main features in the Consumption plan with different service limits, the Flex Consumption plan also supports always ready instances. These instances are intended to reduce the delay during a cold start, but they show up as extra charges in the bill even when the function is paused. For more information about the hosting options, see https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale.
![alt text](images/function_setup_1.png)
3. Select the same resource group "AirQuality" and enter a name for the function app. I am going to use Python 3.13 to build the app.
![alt text](images/function_setup_2.png)
4. Click "Create new" to create a new storage account since I don't have one. I'm keeping the default account name.
![alt text](images/function_setup_3.png)
5. 
![alt text](images/function_setup_4.png)
6. 
![alt text](images/function_setup_5.png)
7. 
![alt text](images/function_setup_6.png)
8. 
![alt text](images/function_setup_7.png)
9. 
Setup Github Action in the Deployment section. It will create a .github/workflows folder with a .yml file in the github repository. If not configured at this stage, it can be setup later after the function app is deployed.
![alt text](images/function_setup_8.png)
10. 
![alt text](images/function_setup_9.png)
11. 
![alt text](images/function_setup_10.png)
12. 
![alt text](images/function_setup_11.png)
13. 


A function app, a storage account and an app service plan are created in this step

## Adjust Settings in Azure Portal

SQL server:
- Add new firewall rules
![alt text](images/sqlserver_security_networking.png)
![alt text](images/sqlserver_security_networking_firewall.png)



SQL database:

Create a table in the database:
```sql
DROP TABLE IF EXISTS air_measurements;
CREATE TABLE air_measurements
(
    idx BIGINT IDENTITY(1,1) PRIMARY KEY,
    ingested_time DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    time_stamp DATETIME2,
    location_id INT,
    location_name NVARCHAR(255),
    location_type NVARCHAR(100),
    pm01 FLOAT,
    pm02 FLOAT,
    pm10 FLOAT,
    pm01_corrected FLOAT,
    pm02_corrected FLOAT,
    pm10_corrected FLOAT,
    pm003_count INT,
    atmp FLOAT,
    rhum FLOAT,
    rco2 FLOAT,
    atmp_corrected FLOAT,
    rhum_corrected FLOAT,
    rco2_corrected FLOAT,
    wifi INT,
    serial_no NVARCHAR(100),
    model NVARCHAR(100),
    firmware_version NVARCHAR(100),
    tvoc FLOAT,
    tvoc_index INT,
    nox_index INT
)
```


Allow function app to access the database:
```sql
CREATE USER [airquality-function] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [airquality-function];
ALTER ROLE db_datawriter ADD MEMBER [airquality-function];
```



While still in the database page, save the following information in a seperate local text file and set it aside:
- **SQL database connection string**: Azure Portal &rarr; SQL database &rarr; Settings &rarr; Connection strings &rarr; ODBC &rarr; Save "ODBC (SQL authentication)" (replace `{your_password_here}` with the SQL authentication password assigned during initial setup)

![alt text](images/sqldatabase_connectionstring.png)


## Enable AirGradient API Access
AirGradient Dashboard &rarr; General Settings &rarr; Connectivity &rarr; API Access &rarr; Toggle to "Enabled".

While still in the dashboard, save the following information in a seperate local text file and set it aside:
- **API token**: AirGradient Dashboard &rarr; General Settings &rarr; Connectivity &rarr; API Access &rarr; Save "Token"
- **Location ID**: AirGradient Dashboard &rarr; Locations &rarr; Save "Location ID"
- **URL**: Save "`https://api.airgradient.com/public/api/v1/locations/{location_id}/measures/current`" (replace `{location_id}` with the acutal Location ID from the previous step)


## Prerequisite installation
install extensions in vs code:
Python (match function app version)
Github Actions
Azure Functions
Azurite (for local testing)

install ODBC driver (https://learn.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server?view=sql-server-ver17)

## Build Function App in VS Code
clone repository to local directory
```bash
cd ~/Work
git clone https://github.com/marilyn-mizhou/airquality_azurefunction.git
```
Enter user name and personal access tokens when prompted.

Open 



create timer function app in local directory
automatically generate necessary function files

edit:
local.settings.json
function_app.py
requirements.txt
.funcignore
.gitignore


```python
import logging
import azure.functions as func
import pyodbc
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
```

```python
app = func.FunctionApp()

@app.timer_trigger(schedule="0 * * * * *", 
                   arg_name="myTimer", 
                   run_on_startup=False, 
                   use_monitor=False)
```



```python
token = os.environ["ag_api_token"]
location_id = os.environ["ag_location_id"]
conn_str = os.environ["sql_connection_string"]
```


```python
# --- 1. Fetch from AirGradient Cloud API ---
url = f"https://api.airgradient.com/public/api/v1/locations/{location_id}/measures/current"

try:
    response = requests.get(url, params={'token': token}, timeout=15)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    raise SystemExit(e)

data = response.json()
logging.info(f"Received: {data}")
```


```python
# --- 2. Parse fields ---
time_stamp = datetime.fromisoformat(data.get("timestamp")).astimezone(ZoneInfo("Canada/Pacific"))
ingested_time = datetime.now(timezone.utc).astimezone(ZoneInfo("Canada/Pacific"))
row = {
    "ingested_time": ingested_time,
    "location_id": data.get("locationId"),
    "location_name": data.get("locationName"),
    "location_type": data.get("locationType"),
    "pm01": data.get("pm01"),
    "pm02": data.get("pm02"),
    "pm10": data.get("pm10"),
    "pm01_corrected": data.get("pm01_corrected"),
    "pm02_corrected": data.get("pm02_corrected"),
    "pm10_corrected": data.get("pm10_corrected"),
    "pm003_count": data.get("pm003Count"),
    "atmp": data.get("atmp"),
    "rhum": data.get("rhum"),
    "rco2": data.get("rco2"),
    "atmp_corrected": data.get("atmp_corrected"),
    "rhum_corrected": data.get("rhum_corrected"),
    "rco2_corrected": data.get("rco2_corrected"),
    "wifi": data.get("wifi"),
    "time_stamp": time_stamp,
    "serial_no": data.get("serialno"),
    "model": data.get("model"),
    "firmware_version": data.get("firmwareVersion"),
    "tvoc": data.get("tvoc"),
    "tvoc_index": data.get("tvocIndex"),
    "nox_index": data.get("noxIndex"),
}
logging.info(f"Converted: {row}")
```


```python
# --- 3. Insert into Azure SQL ---
try:
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO air_measurements (
                ingested_time, time_stamp,
                location_id, location_name, location_type,
                pm01, pm02, pm10,
                pm01_corrected, pm02_corrected, pm10_corrected,
                pm003_count,
                atmp, rhum, rco2,
                atmp_corrected, rhum_corrected, rco2_corrected,
                wifi, serial_no, model, firmware_version,
                tvoc, tvoc_index, nox_index
            ) VALUES (
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?
            )
            """,
            (
                row["ingested_time"], row["time_stamp"],
                row["location_id"], row["location_name"], row["location_type"],
                row["pm01"], row["pm02"], row["pm10"],
                row["pm01_corrected"], row["pm02_corrected"], row["pm10_corrected"],
                row["pm003_count"],
                row["atmp"], row["rhum"], row["rco2"],
                row["atmp_corrected"], row["rhum_corrected"], row["rco2_corrected"],
                row["wifi"], row["serial_no"], row["model"], row["firmware_version"],
                row["tvoc"], row["tvoc_index"], row["nox_index"]
            )
        )
    logging.info("Row inserted successfully.")
except pyodbc.Error as e:
    logging.error(f"SQL insert failed: {e}")
```

```python
def timer_trigger_1min_pull_from_ag(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        return
    
    token = os.environ["ag_api_token"]
    location_id = os.environ["ag_location_id"]
    conn_str = os.environ["sql_connection_string"]

    # --- 1. Fetch from AirGradient Cloud API ---
    url = f"https://api.airgradient.com/public/api/v1/locations/{location_id}/measures/current"

    try:
        response = requests.get(url, params={'token': token}, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    data = response.json()
    logging.info(f"Received: {data}")


    # --- 2. Parse fields ---
    time_stamp = datetime.fromisoformat(data.get("timestamp")).astimezone(ZoneInfo("Canada/Pacific"))
    ingested_time = datetime.now(timezone.utc).astimezone(ZoneInfo("Canada/Pacific"))
    row = {
        "ingested_time": ingested_time,
        "location_id": data.get("locationId"),
        "location_name": data.get("locationName"),
        "location_type": data.get("locationType"),
        "pm01": data.get("pm01"),
        "pm02": data.get("pm02"),
        "pm10": data.get("pm10"),
        "pm01_corrected": data.get("pm01_corrected"),
        "pm02_corrected": data.get("pm02_corrected"),
        "pm10_corrected": data.get("pm10_corrected"),
        "pm003_count": data.get("pm003Count"),
        "atmp": data.get("atmp"),
        "rhum": data.get("rhum"),
        "rco2": data.get("rco2"),
        "atmp_corrected": data.get("atmp_corrected"),
        "rhum_corrected": data.get("rhum_corrected"),
        "rco2_corrected": data.get("rco2_corrected"),
        "wifi": data.get("wifi"),
        "time_stamp": time_stamp,
        "serial_no": data.get("serialno"),
        "model": data.get("model"),
        "firmware_version": data.get("firmwareVersion"),
        "tvoc": data.get("tvoc"),
        "tvoc_index": data.get("tvocIndex"),
        "nox_index": data.get("noxIndex"),
    }
    logging.info(f"Converted: {row}")


    # --- 3. Insert into Azure SQL ---
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO air_measurements (
                    ingested_time, time_stamp,
                    location_id, location_name, location_type,
                    pm01, pm02, pm10,
                    pm01_corrected, pm02_corrected, pm10_corrected,
                    pm003_count,
                    atmp, rhum, rco2,
                    atmp_corrected, rhum_corrected, rco2_corrected,
                    wifi, serial_no, model, firmware_version,
                    tvoc, tvoc_index, nox_index
                ) VALUES (
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    row["ingested_time"], row["time_stamp"],
                    row["location_id"], row["location_name"], row["location_type"],
                    row["pm01"], row["pm02"], row["pm10"],
                    row["pm01_corrected"], row["pm02_corrected"], row["pm10_corrected"],
                    row["pm003_count"],
                    row["atmp"], row["rhum"], row["rco2"],
                    row["atmp_corrected"], row["rhum_corrected"], row["rco2_corrected"],
                    row["wifi"], row["serial_no"], row["model"], row["firmware_version"],
                    row["tvoc"], row["tvoc_index"], row["nox_index"]
                )
            )
        logging.info("Row inserted successfully.")
    except pyodbc.Error as e:
        logging.error(f"SQL insert failed: {e}")
```



## Microsoft Power BI