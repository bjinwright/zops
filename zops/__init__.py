import os
import shutil
import subprocess
import boto3
import re

from jinja2 import FileSystemLoader, Environment
from unipath import Path

from .util import import_util

alpha_num_pattern = re.compile('[\W_]+')

class Zops(object):

    def __init__(self, app_name, stage_name,
                 function_bucket=None, static_bucket=None,
                 username=None, aws_region_name='us-east-1',
                 profile_name='default',user_temp_class='zops.user.UserTemplate'):

        self.app_name = app_name
        self.stage_name = stage_name
        self.user_stack_name = alpha_num_pattern.sub('', "zappa{app_name}{stage_name}user".format(
            app_name=self.app_name,
            stage_name=self.stage_name))

        self.function_bucket = function_bucket
        self.static_bucket = static_bucket
        self.aws_region_name = aws_region_name
        self.username = username or self.user_stack_name
        self.profile_name = profile_name
        self.user_temp_class = user_temp_class
        session = boto3.session.Session(profile_name=self.profile_name)
        self.cf = session.resource('cloudformation')

    def create_user_stack(self):
        #Create the CloudFormation stack
        return self.cf.create_stack(
            StackName=self.user_stack_name,
            TemplateBody=self.render_user(),
            Capabilities=['CAPABILITY_IAM']
        )

    def user_stack_outputs(self):
        #Get the Cloudformation user stack's outputs
        return self.cf.Stack(name=self.user_stack_name).outputs

    def delete_user_stack(self):
        return self.cf.Stack(name=self.user_stack_name).delete()

    def create_initial_app(self):
        #Create app directory
        os.makedirs('app')
        template_path = Path(__file__).ancestor(1).child('templates')
        #Create Jinja2 Environment
        env = Environment(autoescape=False,
                          loader=FileSystemLoader(template_path))
        #Get flask and zappa_settings templates
        flask_app_template = env.get_template('flask.py.jinja2')
        zappa_settings_template = env.get_template(
            'zappa_settings.json.jinja2')
        #Create Flask app and zappa_settings.json files in the app directory
        with open('app/{app_name}.py'.format(app_name=self.app_name), 'w+') as f:
            f.write(flask_app_template.render(app_name=self.app_name, stage_name=self.stage_name))
        with open('app/zappa_settings.json'.format(app_name=self.app_name), 'w+') as f:
            f.write(zappa_settings_template.render(app_name=self.app_name,
                                                   stage_name=self.stage_name,
                                                   function_bucket=self.function_bucket,
                                                   aws_region_name=self.aws_region_name))
        #Copy the HTML template to the app/templates directory
        shutil.copytree(template_path.child('templates'), 'app/templates')

    def deploy_initial_app(self):
        #Get the user stack's keys
        creds = self.user_stack_outputs()
        os.environ['AWS_SECRET_ACCESS_KEY'] = creds[0]['OutputValue']
        os.environ['AWS_ACCESS_KEY_ID'] = creds[1]['OutputValue']
        # try:
            #Run zappa deploy command
        subprocess.check_output(['zappa', 'deploy', self.stage_name, '-s', 'app/zappa_settings.json'])
        # except Exception as e:
        #     #If there is an error with the zappa deploy command print the output
        #     print(e.output)

    def undeploy_initial_app(self):
        # Get the user stack's keys
        creds = self.user_stack_outputs()
        os.environ['AWS_SECRET_ACCESS_KEY'] = creds[0]['OutputValue']
        os.environ['AWS_ACCESS_KEY_ID'] = creds[1]['OutputValue']
        try:
            # Run zappa deploy command
            subprocess.check_output(['zappa', 'undeploy', self.stage_name, '-y','-s', 'app/zappa_settings.json'])
        except Exception as e:
            # If there is an error with the zappa deploy command print the output
            print(e.output)

    def delete_initial_app(self):
        shutil.rmtree('app')

    def render_user(self):
        return import_util(self.user_temp_class)().render(self.app_name,self.stage_name,
                                           self.username,self.function_bucket,
                                           self.static_bucket,self.aws_region_name)

