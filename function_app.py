import logging
import azure.functions as func
import pyodbc
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests

app = func.FunctionApp()

@app.timer_trigger(schedule="0 * * * * *", 
                   arg_name="myTimer", 
                   run_on_startup=False,
                   use_monitor=False) 

def timer_trigger(myTimer: func.TimerRequest) -> None:
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