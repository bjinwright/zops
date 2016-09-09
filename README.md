# zops
Utils for devops teams that want to deploy using Zappa

##Install

```
pip install zops
```

##Usage

###Zops

This commands lists the commands for you. There is only one option for this command and it is **--profile_name**. The profile_name option sets the credentials profile from your ~/.aws/credentials file. This option can be passed to all subcommands.
```
>>>zops
Usage: zops [OPTIONS] COMMAND [ARGS]...

Options:
  --profile_name TEXT  Credentials profile name.
  --help               Show this message and exit.

Commands:
  create_user
  delete_user
  deploy_initial
  undeploy_initial
  user_credentials
```

###Create User

Create an IAM user tailored to your app, stage, region, function and static buckets.

```
>>>zops create_user blog dev
Username: dev_user
Function Bucket: your_functions_bucket
Static Bucket: your_apps_static_bucket
AWS Region Name [us-east-1]: us-east-1
Creating user: zappablogdevuser
```

###User Credentials

Get credentials for the user you created with the create_user command.

```
>>>zops user_credentials blog dev
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
>>>zops deploy_initial blog dev
Function Bucket: your_function_bucket
AWS Region Name [us-east-1]: us-east-1
Creating initial app...
Deploying initial app...
100%|██████████████████████████████████████████████████████████████████| 3.71M/3.71M [00:03<00:00, 1.08MB/s]
100%|████████████████████████████████████████████████████████████| 1008/1008 [01:39<00:00,  5.25 endpoint/s]
Deleting local copy of initial app...

```

###Undeploy Initial

Undeploy the Zappa app with the given name and stage

```
>>>zops undeploy_initial blog dev
Function Bucket: your_function_bucket
AWS Region Name [us-east-1]:
Creating initial app...
Undeploying initial app...
Deleting local copy of initial app...
```