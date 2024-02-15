"""
Module used to interact with the Terarium Data Service (TDS).
"""
import os
import requests


TDS_URL = os.environ.get("TDS_URL", "http://hmi-server:3000")
TDS_USER = os.environ.get("TDS_USER", "adam")
TDS_PASSWORD = os.environ.get("TDS_PASSWORD", "asdf1ASDF")


def auth_session():
	session = requests.Session()
	session.auth = (TDS_USER, TDS_PASSWORD)
	session.headers.update({"Content-Type": "application/json", "X-Enable-Snake-Case": "true"})
	return session
