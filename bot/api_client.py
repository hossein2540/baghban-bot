import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()

class BaghbanAPI:
    def __init__(self, username, app_password):
        self.base_url = os.getenv("SITE_URL") + "/wp-json"
        self.auth = HTTPBasicAuth(username, app_password)

    def search_plants(self, search_term):
        url = f"{self.base_url}/baghban/v1/search-plants"
        resp = requests.get(url, params={"search": search_term}, auth=self.auth)
        return resp.json()

    def add_plant(self, plant_data):
        url = f"{self.base_url}/baghban/v1/add-plant"
        resp = requests.post(url, json=plant_data, auth=self.auth)
        return resp.json()

    def get_my_plants(self):
        url = f"{self.base_url}/baghban/v1/my-plants"
        resp = requests.get(url, auth=self.auth)
        return resp.json()

    def get_plant_details(self, user_plant_id):
        url = f"{self.base_url}/baghban/v1/plant-details"
        resp = requests.get(url, params={"user_plant_id": user_plant_id}, auth=self.auth)
        return resp.json()

    def get_events(self):
        url = f"{self.base_url}/baghban/v1/events"
        resp = requests.get(url, auth=self.auth)
        return resp.json()

    def get_subscription_status(self):
        url = f"{self.base_url}/baghban/v1/subscription-status"
        resp = requests.get(url, auth=self.auth)
        return resp.json()

    def subscribe(self, plan_id):
        url = f"{self.base_url}/baghban/v1/subscribe"
        resp = requests.post(url, json={"plan_id": plan_id}, auth=self.auth)
        return resp.json()

    def get_notifications(self):
        url = f"{self.base_url}/baghban/v1/notifications"
        resp = requests.get(url, auth=self.auth)
        return resp.json()