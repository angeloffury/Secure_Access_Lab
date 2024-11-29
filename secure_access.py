import requests
import json
import os
import time
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
import time
import logging

# Export/Set the environment variables
csa_client_id = os.environ.get('csa_api_key')
csa_client_secret = os.environ.get('csa_api_secret')
csa_token_url = 'https://api.sse.cisco.com/auth/v2/token'
total_clients=int(os.environ.get('total_clients'))

class SecureAccessAPI:
    def __init__(self, url, ident, secret):
        self.url = url
        self.ident = ident
        self.secret = secret
        self.token = None

    def ValidateToken(self):
        if self.token is not None :
            current_time= int(time.time())
            if self.token["expires_at"] > current_time:
                return True
            else:
                return False
        else:
            return False

    def GetToken(self):
        if not self.ValidateToken():
            auth = HTTPBasicAuth(self.ident, self.secret)
            client = BackendApplicationClient(client_id=self.ident)
            oauth = OAuth2Session(client=client)
            self.token = oauth.fetch_token(token_url=self.url, auth=auth)
            return self.token
        else:
            return self.token
    

# Exit out if the client_id, client_secret are not set
for var in ['csa_api_key', 'csa_api_secret']:
    if os.environ.get(var) == None:
        print("Required environment variable: {} not set".format(var))
        exit()

# Get token
api = SecureAccessAPI(csa_token_url, csa_client_id, csa_client_secret)
       
       
def get_all_access_rules():
    access_token = api.GetToken()["access_token"]
    url = "https://api.sse.cisco.com/policies/v2/rules"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return  response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def filter_client_access_rules(access_rules):
    filtered_ruleIds=[]
    all_access_rules =access_rules["results"]
    for rule in all_access_rules:
        if ("client0-" not in rule["ruleName"]) and ("DNS Inbound" not in rule["ruleName"]) and ("For all" not in rule["ruleName"]):
            filtered_ruleIds.append(rule["ruleId"])
            print("\t\t",rule["ruleName"])
    return filtered_ruleIds


def delete_rules_bulk_v1(rule_ids):
    access_token = api.GetToken()["access_token"]
    url = "https://api.umbrella.com/v1/sse/organizations/8206404/rules/bulk"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "rulesIds": ",".join(str(rule_id) for rule_id in rule_ids)
    }
    new_url=url+"?rulesIds="+params["rulesIds"]
    try:
        print("\t\tAll the above Access Policy DELETE in progress...")
        print (new_url)
        response=requests.delete(new_url, headers=headers)
        # response = requests.delete(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        print("\t\tAll Access Policy rules DELETED successfully (except Client0).")
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        logging.exception(e)

def delete_rules_bulk(rule_ids):
   
    access_token = api.GetToken()["access_token"]
    url = "https://api.sse.cisco.com/policies/v2/rules/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    print("\t\tAll the Access Policy DELETE in progress...")
    print("\t\t", end='')
    for rule_id in rule_ids:
        new_url=url+str(rule_id)
        try:
            print('*', end='')
            response=requests.delete(new_url, headers=headers)
            # response = requests.delete(url, headers=headers, params=params)
            #response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        except requests.exceptions.RequestException as e:
            print("Error:", e)
            logging.exception(e)
    print("\n\t\tAll Access Policy rules DELETED successfully (except Client0).")
    return

def get_all_private_resources():
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/policies/v2/privateResources"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def delete_private_resources(pvt_resources):
    access_token = api.GetToken()["access_token"]    
    for resource in pvt_resources:
        resource_name=resource["name"]
        if ("client0-" not in resource_name):
            resource_id= resource["resourceId"]
            url = f"https://api.sse.cisco.com/policies/v2/privateResources/{resource_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.delete(url, headers=headers)
                response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
                print("\t\tPrivate resource ",resource_name," deleted successfully.")
            except requests.exceptions.RequestException as e:
                print("Error:", e)


def delete_client_private_resources():
    all_pvt_resources = get_all_private_resources()
    deleted= False
    while int(all_pvt_resources["total"])!=4:
        delete_private_resources(all_pvt_resources["items"])
        deleted=True
        all_pvt_resources = get_all_private_resources()
    if(deleted):
        print("\n\t\tAll Private resources are DELETED (except Client0)")
    else:
        print("\n\t\tNo Private resources to DELETE")


def get_all_private_resource_groups():
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/policies/v2/privateResourceGroups"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
def delete_private_resource_groups(pvt_resource_groups):
    access_token = api.GetToken()["access_token"]    
    for resource_group in pvt_resource_groups:
        resource_group_name=resource_group["name"]
        if ("client0-" not in resource_group_name):
            resource_group_id= resource_group["resourceGroupId"]
            url = f"https://api.sse.cisco.com/policies/v2/privateResourceGroups/{resource_group_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.delete(url, headers=headers)
                response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
                print("\t\tPrivate resource Groups ",resource_group_name," deleted successfully.")
            except requests.exceptions.RequestException as e:
                print("Error:", e)


def delete_client_private_resource_groups():
    all_pvt_resource_groups = get_all_private_resource_groups()
    deleted=False
    while int(all_pvt_resource_groups["total"])!=1:
        delete_private_resource_groups(all_pvt_resource_groups["items"])
        deleted=-True
        all_pvt_resource_groups = get_all_private_resource_groups()
    if(deleted):
        print("\n\t\tAll Private resource Groups are DELETED (except Client0)")
    else:
        print("\n\t\tNo Private resource Groups to DELETE")


def get_all_posture_profiles_v1():
    access_token = api.GetToken()["access_token"]
    url = f"https://api.umbrella.com/v1/organizations/8206404/postureprofiles"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    

def delete_posture_profile_v1(posture_profiles):
    access_token = api.GetToken()["access_token"]
    deleted =False
    for posture_profile in posture_profiles["resources"]:
        posture_profile_name = posture_profile ["resourceInstanceName"]
        if ("client0-" not in posture_profile_name) and ("System provided" not in posture_profile_name) and("No requirements" not in posture_profile_name) :
            posture_profile_id = posture_profile["resourceInstanceId"]
            url = f"https://api.umbrella.com/v1/organizations/8206404/postureprofiles/{posture_profile_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.delete(url, headers=headers)
                response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
                print("\t\tPosture profile",posture_profile_name," deleted successfully.")
                deleted =True
            except requests.exceptions.RequestException as e:
                print("Error:", e)

    if(deleted):
        print("\n\t\tAll Endpoint posture profiles DELETED successfully (except Client0).")
    else:
        print("\n\t\tNo Endpoint posture profiles to DELETE")


def get_all_destination_lists():
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/policies/v2/destinationlists"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
def delete_destination_lists(destination_lists):
    access_token = api.GetToken()["access_token"]
    deleted =False
    for destination_list in destination_lists["data"]:
        if("client0-" not in destination_list["name"] and "Global " not in destination_list["name"]):
            destionation_list_id = destination_list["id"]
            url = f"https://api.sse.cisco.com/policies/v2/destinationlists/{destionation_list_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.delete(url, headers=headers)
                response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
                print("\t\tDestination List ",destination_list["name"]," deleted successfully.")
                deleted =True
            except requests.exceptions.RequestException as e:
                print("Error:", e)

    if(deleted):
        print("\n\t\tAll Destination List DELETED successfully (except Client0).")
    else:
        print("\n\t\tNo Destination List to DELETE")


def get_all_roaming_devices():
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/deployments/v2/roamingcomputers"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    

def delete_roaming_devices(roaming_devices):
    access_token = api.GetToken()["access_token"]
    deleted=False
    for roaming_device in roaming_devices:
        roaming_device_name=roaming_device["name"]
        if "client0" not in roaming_device_name:
            roaming_device_id = roaming_device["deviceId"]
            url = f"https://api.sse.cisco.com/deployments/v2/roamingcomputers/{roaming_device_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.delete(url, headers=headers)
                response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
                print("\t\tRoaming device ",roaming_device_name," deleted successfully.")
                deleted =True
            except requests.exceptions.RequestException as e:
                print("Error:", e)

    if(deleted):
        print("\n\t\tAll Roaming devices DELETED successfully (except Client0).")
    else:
        print("\n\t\tNo Roaming device to DELETE")   

def get_all_admins():
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/admin/v2/users"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def create_read_only(client_num):
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/admin/v2/users"
    email="client"+client_num+"@funwithsse.net"
    password="Funw1thSSE"+client_num+"!"
    body= {"firstname":"Client","lastname":client_num,"email":email,"password":password,"roleId":2,"timezone":"UTC"}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        print("\t\tSuccess! Client",client_num, "is set to READ ONLY admin")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print ("\t\tAPI Rate Limiting! Retrying in 60 seconds...Please wait!")
        time.sleep(61)
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        print("\t\tSuccess! Client",client_num, "is set to READ ONLY admin")
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
def create_full_admin(client_num):
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/admin/v2/users"
    email="client"+client_num+"@funwithsse.net"
    password="Funw1thSSE"+client_num+"!"
    body= {"firstname":"Client","lastname":client_num,"email":email,"password":password,"roleId":1,"timezone":"UTC"}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        print("\t\tSuccess! Client",client_num, "is set to FULL ADMIN")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print ("\t\tAPI Rate Limiting!! Retrying in 60 seconds...Please wait!")
        time.sleep(61)
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
        print("\t\tSuccess! Client",client_num, "is set to FULL ADMIN")
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
def delete_admin(user_id):
    access_token = api.GetToken()["access_token"]
    url = f"https://api.sse.cisco.com/admin/v2/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print ("\t\tAPI Rate Limiting!! Retrying in 60 seconds...Please wait!")
        time.sleep(61)
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error deleting user: {e}")
   

def set_clients_to_read_only():
    all_admins=get_all_admins()
    for admin in all_admins:
        #check if admin's last name is 1- N
        if admin["lastname"].isdigit():
            client_num=int(admin["lastname"])
            if client_num> 0 & client_num<= total_clients:
                if admin["roleId"]==2:
                    print("\t\tClient",client_num, "is already Read-Only admin")
                else:
                    print("\tSetting Client",client_num,"to Read-Only admin")
                    time.sleep(4)
                    delete_admin(admin["id"])
                    time.sleep(4)
                    create_read_only(str(client_num))
                   


def set_clients_to_full_admin():
    all_admins=get_all_admins()
    for admin in all_admins:
        #check if admin's last name is 1- N
        if admin["lastname"].isdigit():
            client_num=int(admin["lastname"])
            if client_num> 0 & client_num<= total_clients:
                if admin["roleId"]==1:
                    print("\t\tClient",client_num, "is already Full Admin")
                else:
                    print("\tSetting Client",client_num,"to Full Admin")
                    time.sleep(4)
                    delete_admin(admin["id"])
                    time.sleep(4)
                    create_full_admin(str(client_num))
        
#The below function return 401 since we do not have the Auth token to run the API
def get_all_dlp_policies () :
    access_token = api.GetToken()["access_token"]
    url = f"https://management.api.umbrella.com/dlp-policy-service/us/v2/organizations/8206404/rules"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
def delete_dlp_policies(dlp_policies):
    access_token = api.GetToken()["access_token"]
    deleted =False
    print(dlp_policies)
    for dlp_policy in dlp_policies:
        print(dlp_policy)