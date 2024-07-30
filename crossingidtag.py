# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 20:33:26 2024

@author: bigal
"""

import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

def download_excel_file(download_path):
    try:
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": download_path, "safebrowsing.enabled": "false"}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_service = Service(r'C:\Users\bigal\traincrossing\chromedriver-win64\chromedriver.exe')
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        driver.get("https://www.fra.dot.gov/bcirIncidents")
        
        # Locate and click the "Export to Excel" button
        try:
            download_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Export to Excel')]"))
            )
            download_button.click()
            print("Download button clicked.")
        except Exception as e:
            print(f"Error locating or clicking the download button: {e}")
            driver.quit()
            return False

        # Wait for the file to download
        time.sleep(30)  # Adjust sleep time as necessary to ensure the file is downloaded
        print("Waiting for the file to download...")

        driver.quit()
        return True
    except Exception as e:
        print(f"Failed to download the file: {e}")
        return False

def convert_excel_to_csv(download_path):
    # Find the latest downloaded Excel file
    files = [f for f in os.listdir(download_path) if f.endswith('.xlsx')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(download_path, x)), reverse=True)
    excel_file = os.path.join(download_path, files[0]) if files else None

    if not excel_file:
        print("No Excel file found in the download directory.")
        return None

    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
        csv_file = os.path.join(download_path, 'converted_data.csv')
        df.to_csv(csv_file, index=False)
        print(f"Converted Excel to CSV: {csv_file}")
        return csv_file
    except Exception as e:
        print(f"Failed to convert Excel to CSV: {e}")
        return None

def fetch_lat_long(crossing_id, driver):
    url = f"https://fragis.fra.dot.gov/FRA-PopupViewer/index.html?ZoomToCrossing={crossing_id}"
    driver.get(url)
    
    try:
        latitude_element = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "//th[text()='LATITUDE']/following-sibling::td"))
        )
        latitude = latitude_element.text

        longitude_element = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "//th[text()='LONGITUD']/following-sibling::td"))
        )
        longitude = longitude_element.text

        return latitude, longitude
    except Exception as e:
        print(f"Error fetching data for crossing ID {crossing_id}: {e}")
        return None, None

def clean_data_and_get_coordinates(csv_file, output_csv_path):
    df = pd.read_csv(csv_file)
    df = df[['Date/Time', 'Duration', 'Crossing ID']]

    chrome_service = Service(r'C:\Users\bigal\traincrossing\chromedriver-win64\chromedriver.exe')
    driver = webdriver.Chrome(service=chrome_service)

    df['Latitude'] = None
    df['Longitude'] = None

    for index, row in df.iterrows():
        crossing_id = row['Crossing ID']
        lat, long = fetch_lat_long(crossing_id, driver)
        if lat and long:
            df.at[index, 'Latitude'] = lat
            df.at[index, 'Longitude'] = long
        time.sleep(2)

    driver.quit()

    df_result = df[['Date/Time', 'Duration', 'Latitude', 'Longitude']]
    output_dir = os.path.dirname(output_csv_path)
    
    if not os.path.exists(output_dir):
        print(f"Directory does not exist: {output_dir}")
        return
    
    df_result.to_csv(output_csv_path, index=False)
    print(f"Cleaned data has been saved to '{output_csv_path}'")

download_path = "C:\\Users\\bigal\\traincrossing"
output_csv_path = "C:\\Users\\bigal\\traincrossing\\docs\\cleaned_data.csv"

if download_excel_file(download_path):
    csv_file = convert_excel_to_csv(download_path)
    if csv_file:
        clean_data_and_get_coordinates(csv_file, output_csv_path)
else:
    print("File download failed.")
