# argdict example: {'target': ['10.0.0.74:8000'], 'hub': ['10.0.0.193']}

import sys
from datetime import datetime
from selenium import webdriver
timeformat = "[%m-%d_%H:%M:%S.%f] "


def get_formatted_time():
	return datetime.strftime(datetime.now(), timeformat)


argsdict = {argument.split("=")[0]: argument.split("=")[1] for argument in sys.argv if '=' in argument}

test_url = "http://" + argsdict["target"]
hub_address = argsdict["hub"] if "hub" in argsdict else ""
artifacts_folder = argsdict["artifacts_folder"]
server_mode = "local" if not hub_address else "remote"
lookup_text = "magnam"

print(datetime.strftime(datetime.now(), timeformat) + "Starting Selenium Web Driver...")
if server_mode is "remote":
	selenium_driver = webdriver.Remote(command_executor="http://" + hub_address + ":4444/wd/hub", desired_capabilities={"browserName": "chrome"})
else:
	selenium_driver = webdriver.Chrome()
print(datetime.strftime(datetime.now(), timeformat) + "Getting test page...")
selenium_driver.get(test_url)
print(get_formatted_time() + "Navigating to Hats page")
hats_button = selenium_driver.find_element_by_css_selector('a.item[href="/en_US/taxons/hats"]')
hats_button.click()

hats_elements = selenium_driver.find_elements_by_class_name("sylius-product-name")

matching_hats = [hat for hat in hats_elements if lookup_text in hat.text]

try:
	assert len(matching_hats) > 0
except AssertionError:
	print(get_formatted_time() + "Test Failed, could not locate lookup text...")
	selenium_driver.get_screenshot_as_file(artifacts_folder + "/Failed_state.png")
	selenium_driver.quit()
	raise AssertionError
	
print(get_formatted_time() + "Taking screenshot...")
selenium_driver.get_screenshot_as_file(artifacts_folder + "/Hats_page.png")
selenium_driver.quit()
print(get_formatted_time() + "Test Passed")
