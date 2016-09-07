# zops
Utils for devops teams that want to deploy using Zappa

##Usage

###Deploy an empty WSGI app
```
zops <app_name> <stage_name> deploy_initial <region_name>
```
###Create an IAM user with privileges for a Zappa project

```
zops <app_name> <stage_name> create_user <username> -p <profile_name>
```

