from setuptools import setup, find_packages

install_requires = []
with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in frappedesk/__init__.py
from frappedesk import __version__ as version

install_requires.append(
	"zang @ git+https://git@github.com/zang-cloud/zang-python.git@master#egg=zang"
)

setup(
	name="frappedesk",
	version=version,
	description="Customer Service Software",
	author="Frappe Technologies",
	author_email="hello@frappe.io",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
)
