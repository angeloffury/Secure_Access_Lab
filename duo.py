
import requests
import time
import util

#Get all bypass codes of users
def get_bypass_codes(users,hostname,skey,ikey) :
    all_bypass_codes=[]
    for x in users:
        x_path='/admin/v1/users/'+x['user_id']+'/bypass_codes'
        print(x['username'])
        api_auth = util.sign('GET',hostname,x_path,{},skey,ikey)
        bypass_code = requests.get("https://"+hostname+x_path, headers=api_auth)
        time.sleep(0.1)
        response = bypass_code.json()['response']
        if response!=[]:
            number_of_bypass_codes =len(response)
            x=0
            while x<number_of_bypass_codes:
                print("Bypass code id :",response[x].get('bypass_code_id'))
                print("Expire on :",response[x].get('expiration'))
                all_bypass_codes.append(response[x])
                x+=1
        else:
            print("Bypass code : Empty")
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
            print("\t\t",x['username'], "bypass code is changed")
        else:
            print("\t\tBypass code : Empty")
        conn.close()

#Delete all bypass codes by calling DELETE /admin/v1/bypass_codes/[bypass_code_id]
def delete_bypass_codes(bypas_codes,hostname,skey,ikey):
    print("Deleting bypass code for users...")
    for x in bypas_codes:
        print(x)
        x_path='/admin/v1/bypass_codes/'+x.get('bypass_code_id')
        print("==============================================================\n"+x_path)
        api_auth = util.sign('DELETE',hostname,x_path,{},skey,ikey)
        bypass_code = requests.delete("https://"+hostname+x_path,headers=api_auth)
        time.sleep(0.1)
        response = bypass_code.json()
        if response!={}:
            print (response)
        else:
            print("Bypass code : Empty")
        bypass_code.close()
    print("==============================================================\n")  


#Get all users_ids    
def get_all_users(hostname,skey,ikey):
    path = '/admin/v1/users'
    api_auth = util.sign('GET',hostname,path,{},skey,ikey)
    all_users = requests.get("https://"+hostname+path, headers=api_auth)
    users=all_users.json()['response']
    all_users.close()
    return users
