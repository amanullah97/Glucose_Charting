from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.select import Select
import easygui
import re
import sys


class ReadingsExtraction:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    readings_data = []
    not_readings_data = []

    def start_request(self, url):
        print("Glucometer-Charting")
        self.driver.get(url)
        self.login()

    def login(self):
        patient_id = self.get_valid_id()
        username = self.driver.find_element(By.NAME, "username")
        username.send_keys("******")
        password = self.driver.find_element(By.NAME, "password")
        password.send_keys("******")
        button = self.driver.find_element(By.ID, "login-btn")
        button.click()
        time.sleep(3)
        self.after_login(patient_id)

    def after_login(self, patient_id):
        url = f"https://portal.smartmeterrpm.com/patient/weights-vitals/edit/{patient_id}"
        self.driver.get(url)
        self.extract_reading()
        average = str(self.get_average())

        total_time = 60 - len(self.readings_data)
        if len(self.readings_data) <= 6:
            total_time = 30
            for item in self.not_readings_data:
                item["Date"] = item["Date"].replace("(2 min)", "(1 min)")

        total_list = self.readings_data + self.not_readings_data
        sorted_data = sorted(total_list, key=lambda x: x['Date'])

        if total_list:
            self.write_to_file(sorted_data, average, patient_id, total_time)
            print("Charting Created Successfully!")


        if len(self.readings_data) >= 10 and len(self.readings_data) < 16:
            message = "Please Ask your patient to take readings regularly!"
            title = "Warning"
            easygui.msgbox(message, title)

    def get_average(self):
        if len(self.readings_data) == 0:
            return 0
        sum = 0
        for i in self.readings_data:
            sum += int(i["Glucose_Reading"])
        average_reading = sum // len(self.readings_data)
        avg = str(average_reading) + " " + "mg/dl"
        return avg

    def get_dates(self):
        current_date = self.get_valid_date()
        date_format = "%Y-%m-%d"
        start_date = datetime.strptime(current_date, date_format)
        last_date = start_date + timedelta(days=30)

        dates = []
        while start_date < last_date:
            formatted_date = start_date.strftime("%m/%d/%Y")
            dates.append(formatted_date)
            start_date += timedelta(days=1)

        return dates, current_date, last_date.strftime("%Y-%m-%d")

       
    def extract_reading(self):
        dates, start_date, end_date = self.get_dates()
        try:
            select = Select(self.driver.find_element(By.NAME, "select-graph"))
            select.select_by_value("blood_glucose")
            button = self.driver.find_element(By.ID, "search")
            button.click()
            time.sleep(5)
            self.driver.implicitly_wait(20)
            start_date_field = self.driver.find_element(By.ID, "start-date")
            end_date_field = self.driver.find_element(By.ID, "end-date")

            start_date_field.click()
            start_date_field.clear()
            start_date_field.send_keys(start_date)

            end_date_field.click()
            end_date_field.clear()
            end_date_field.send_keys(end_date)

            button.click()
            time.sleep(5)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            for date in dates:
                date_column = soup.find("td", string=date)
                if date_column:
                    glucose_reading = self.driver.find_element(By.XPATH,
                                                               f'//tr[contains(., "{date}")]//following-sibling::tr/td[@class="text-center"]').text
                    patient_reading = {
                        "Date": date + " " + "(1 min)",
                        "Glucose_Reading": glucose_reading
                    }
                    self.readings_data.append(patient_reading)
                else:
                    patient_reading = {
                        "Date": date + " " + "(2 min)",
                        "Glucose_Reading": "No Reading Checked twice"
                    }
                    self.not_readings_data.append(patient_reading)
        except Exception:
            message = "Exception"
            title = "Please check your connection and try again."
            easygui.msgbox(message, title)

    def write_to_file(self, total_list, avg_reading, patient_id, total_time):
        with open(f"{patient_id}-glucometer_reading.txt", "w", encoding="utf-8") as file:
            file.write(f"Total Readings: {len(self.readings_data)}\n")
            file.write(f"Average Reading: {avg_reading}\n")
            file.write(f"Documentation Time: {total_time}\n")
            file.write("\n\n")

            for item in total_list:
                file.write(f"{item['Date']}\n")
                file.write(f"{item['Glucose_Reading']}\n")

    def get_valid_id(self):
        while True:
            message = "Glucometer-Charting "
            title = "Please Enter Patient-ID: (numbers-only)"
            id = easygui.enterbox(title, message)

            if id is None:
                sys.exit()

            if re.match(r"^[0-9]+$", id):
                return id
            else:
                easygui.msgbox("Invalid ID. Please Enter numbers only!", "Error")

    def get_valid_date(self):
        while True:
            message = "Date-Range"
            title = "Please Enter Start-Date according to format: (yyyy-mm-dd)"
            date = easygui.enterbox(title, message)
            date_pattern = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"

            if date is None:
                sys.exit()

            if re.match(date_pattern, date):
                return date
            else:
                easygui.msgbox("Invalid date entered. Please Enter Date according to the format (yyyy-mm-dd)", "Error")


x = ReadingsExtraction()
x.start_request("https://portal.smartmeterrpm.com/login")
