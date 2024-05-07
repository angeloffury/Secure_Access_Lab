
import requests
import time
import util
import json
import os

from dotenv import load_dotenv
load_dotenv()
total_clients=int(os.environ.get('total_clients'))

#Get all bypass codes of users
def get_bypass_codes(users,hostname,skey,ikey) :
    all_bypass_codes=[]
    for x in users:
        x_path='/admin/v1/users/'+x['user_id']+'/bypass_codes'
        api_auth = util.sign('GET',hostname,x_path,{},skey,ikey)
        bypass_code = requests.get("https://"+hostname+x_path, headers=api_auth)
        time.sleep(0.1)
        response = bypass_code.json()['response']
        if response!=[]:
            number_of_bypass_codes =len(response)
            x=0
            while x<number_of_bypass_codes:
                all_bypass_codes.append(response[x])
                x+=1
        else:
            print("\t\tBypass code of",x['username']," : Empty")
        bypass_code.close()
    return all_bypass_codes

#Set new bypass codes for users
def set_bypass_codes(users,hostname,skey,ikey,bypass_code):
    print("\tSetting bypass code",bypass_code, "for users...")
    bypass_str = str(bypass_code)
    params ={'reuse_count':'0','valid_secs':'0', 'codes':bypass_str} #Set bypasscode for user with unlimited reuse & no expiration
    for x in users:
        x_path='/admin/v1/users/'+x['user_id']+'/bypass_codes'
        api_auth = util.sign('POST',hostname,x_path,params,skey,ikey)
        api_auth['Content-Type']='application/x-www-form-urlencoded'
        conn = requests.post("https://"+hostname+x_path, headers=api_auth,data=params)
        time.sleep(0.1)
        response = conn.json()
        if response!=[]:
            print("\t\t",x['username'], "bypass code is set")
        else:
            print("\t\tBypass code : Empty")
        conn.close()

#Delete all bypass codes by calling DELETE /admin/v1/bypass_codes/[bypass_code_id]
def delete_bypass_codes(bypas_codes,hostname,skey,ikey):
    if not bypas_codes==[] :
        i=1
        for x in bypas_codes:
            print("\t\tTrying to DELETE bypass code for Client",i,"...")
            x_path='/admin/v1/bypass_codes/'+x.get('bypass_code_id')
            api_auth = util.sign('DELETE',hostname,x_path,{},skey,ikey)
            conn = requests.delete("https://"+hostname+x_path,headers=api_auth)
            time.sleep(0.1)
            response = conn.json()
            if response!={}:
                print("\t\tDELETED bypass code for Client",i)
            conn.close()
            i+=1
    else:
        print("\n\t\tNo Bypass codes to DELETE")
        



#Get all users_ids    
def get_all_users(hostname,skey,ikey):
    path = '/admin/v1/users'
    i,username_list=1,[]
    while i <=total_clients:
        username_list.append('client'+str(i))
        i+=1
    api_auth = util.sign('GET',hostname,path,{},skey,ikey)
    all_users = requests.get("https://"+hostname+path, headers=api_auth)
    time.sleep(0.1)
    all_users=all_users.json()['response']
    client_machines =[]
    for a_user in all_users:
        for username in username_list:
            if a_user['username']==username:
                client_machines.append(a_user)
    return client_machines
