# argdict example: {'target': ['10.0.0.74:8000'], 'hub': ['10.0.0.193']}

import sys
from datetime import datetime
from selenium import webdriver
timeformat = "[%m-%d_%H:%M:%S.%f] "
argsdict = {argument.split("=")[0]: argument.split("=")[1] for argument in sys.argv if '=' in argument}

test_url = "http://" + argsdict["target"]
hub_address = argsdict["hub"]

print(datetime.strftime(datetime.now(), timeformat) + "Starting Selenium Web Driver...\n")
selenium_driver = webdriver.Remote(command_executor="http://" + hub_address + ":4444/wd/hub", desired_capabilities={"browserName": "chrome"})
print(datetime.strftime(datetime.now(), timeformat) + "Getting test page...\n")
selenium_driver.get(test_url)
print(datetime.strftime(datetime.now(), timeformat) + "Taking screenshot...\n")
selenium_driver.get_screenshot_as_file('artifacts/Main_Page.png')
selenium_driver.close()

print(datetime.strftime(datetime.now(), timeformat) + "Test Completed Successfully")
