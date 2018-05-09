from setuptools import setup

setup(
	name="cloudshelltrialutils",
	version="0.2.4.0",
	description="A Utility package for CloudShell Trial Platform code",
	author="Leeor Vardi",
	author_email="leeor.v@quali.com",
	url="https://github.com/QualiSystemsLab/CloudShellTrial/tree/master/Packages/cloudshelltrialutils",
	packages=["cloudshelltrialutils"],
	package_dir={'cloudshelltrialutils': '.'},
	install_requires=["cloudshell-automation-api"]
)