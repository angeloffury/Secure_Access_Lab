# Overview
Admin task automation script for Secure Access lab automation Lab.
Currently Automates AWS reset & Duo bypass codes
Secure Access policy reset & other tasks still needs to be completed manually

# How to Run?

Follow the below steps on your terminal


MAC OS

First installation:
```
$ git clone https://github.com/angeloffury/Secure_Access_Lab.git
$ cd Secure_Access_Lab
$ pip3 install --requirement requirements
$ touch .env
$ nano .env
```
Add the below text inside .env file: 
```
ikey= "<Duo ikey>"
skey= "<Duo skey>"
hostname="api-xxxx.duosecurity.com" <change to use your Duo account>
aws_access_key_id = "AWS access key"
aws_secret_access_key = "AWS secret key"
region_name ="us-east-2" <change if using a different AWS region>
```
Running the script:
```
$ python3 lab_admin
```

