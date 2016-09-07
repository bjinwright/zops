# zops
Utils for devops teams that want to deploy using Zappa

##Install

```
pip install zops
```

##Usage

###Zops

All of zops' commands require two variables, **app_name** and **stage_name**.
```
>>>zops app_name stage_name
```

###Create User

Create an IAM user tailored to your app, stage, region, function and static buckets.

```
>>>zops blog dev create_user
Function Bucket: your_functions_bucket
Static Bucket: your_apps_static_bucket
AWS Region Name [us-east-1]: us-east-1
Creating user: zappablogdevuser
```

###User Credentials

Get credentials for the user you created with the create_user command.

```
>>>zops blog dev user_credentials
Username: zappablogdevuser
+-----------+------------------------------------------+
| Attribute | Value                                    |
+-----------+------------------------------------------+
| SecretKey | your_secret_key_here                     |
| AccessKey | your_access_key_here                     |
+-----------+------------------------------------------+

```

###Deploy Initial

Deploy a small Flask app using the newly created credentials. Use this command if you are planning on using a Continuous Integration/Deployment server.
```
>>>zops blog dev deploy_initial
Function Bucket: your_function_bucket
AWS Region Name [us-east-1]: us-east-1
Creating initial app...
Deploying initial app...
100%|██████████████████████████████████████████████████████████████████| 3.71M/3.71M [00:03<00:00, 1.08MB/s]
100%|████████████████████████████████████████████████████████████| 1008/1008 [01:39<00:00,  5.25 endpoint/s]
Deleting local copy of initial app...

```