import os
import shutil
import subprocess

import awacs
import boto3
from awacs.apigateway import ARN as APIGW_ARN
from awacs.aws import Allow, Policy, Statement
from awacs.awslambda import ARN as LAMBDA_ARN
from awacs.iam import ARN as IAM_ARN
from awacs.s3 import ARN as S3_ARN
from awacs.events import ARN as EVENTS_ARN
from jinja2 import FileSystemLoader, Environment
from troposphere import GetAtt, Output, Ref, Template
from troposphere.iam import PolicyType, User, AccessKey
from unipath import Path


class Zops(object):

    def __init__(self, app_name, stage_name,
                 function_bucket=None, static_bucket=None,
                 username=None, aws_region_name='us-east-1',profile_name='default'):
        self.app_name = app_name
        self.stage_name = stage_name
        self.user_stack_name = 'zappa{0}{1}user'.format(
            self.app_name, self.stage_name)
        self.function_bucket = function_bucket
        self.static_bucket = static_bucket
        self.aws_region_name = aws_region_name
        self.username = username or self.user_stack_name
        self.profile_name = profile_name
        self.t = Template()
        self.t.add_description(
            "Zappa Template for {app_name}-{stage_name} ".format(
                app_name=self.app_name, stage_name=self.stage_name))
        session = boto3.session.Session(profile_name=self.profile_name)
        self.cf = session.resource('cloudformation')

    def get_statement_list(self):
        stm_list = []
        stm_list.extend(self.create_s3_policy())
        stm_list.extend(self.create_iam_policy())
        stm_list.extend(self.create_apigw_policy())
        stm_list.extend(self.create_lambda_policy())
        stm_list.extend(self.create_events_policy())
        return stm_list

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
        try:
            #Run zappa deploy command
            subprocess.check_output(['zappa', 'deploy', self.stage_name, '-s', 'app/zappa_settings.json'])
        except Exception as e:
            #If there is an error with the zappa deploy command print the output
            print(e.output)

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
        zappa_user = self.t.add_resource(User(self.username))
        zappa_user_keys = self.t.add_resource(AccessKey(
            "ZappaUserKeys",
            Status="Active",
            UserName=Ref(zappa_user))
        )
        self.t.add_resource(
            PolicyType(
                "{app_name}{stage_name}".format(
                    app_name=self.app_name,
                    stage_name=self.stage_name),
                Users=[Ref(zappa_user)],
                PolicyName="zappa-{app_name}-{stage_name}".format(
                    app_name=self.app_name,
                    stage_name=self.stage_name),
                PolicyDocument=Policy(
                    Version="2012-10-17",
                    Statement=self.get_statement_list(),
                ),
            )
        )
        self.t.add_output(Output(
            "AccessKey",
            Value=Ref(zappa_user_keys),
            Description="AWSAccessKeyId of new user",
        ))
        self.t.add_output(Output(
            "SecretKey",
            Value=GetAtt(zappa_user_keys, "SecretAccessKey"),
            Description="AWSSecretKey of new user",
        ))
        return self.t.to_json()

    def create_s3_policy(self):
        bucket_list = [

            S3_ARN(self.function_bucket)
        ]
        bucket_list_paths = [
            S3_ARN("{0}/*".format(self.function_bucket)),
        ]
        if self.static_bucket:
            bucket_list.append(S3_ARN(self.static_bucket))
            bucket_list_paths.extend([S3_ARN("{0}/{1}-{2}-static/*".format(
                self.static_bucket,
                self.app_name, self.stage_name)),
                S3_ARN("{0}/{1}-{2}-media/*".format(
                    self.static_bucket,
                    self.app_name, self.stage_name)), ])

        return [
            Statement(
                Effect=Allow,
                Action=[
                    awacs.s3.ListBucket,
                ],
                Resource=bucket_list
            ),
            Statement(
                Effect=Allow,
                Action=[awacs.s3.DeleteObject,
                        awacs.s3.GetObject,
                        awacs.s3.PutObject,
                        awacs.s3.AbortMultipartUpload,
                        awacs.s3.ListMultipartUploadParts,
                        awacs.s3.ListBucketMultipartUploads,

                        ],
                Resource=bucket_list_paths,
            )
        ]

    def create_apigw_policy(self):
        return [
            Statement(
                Effect=Allow,
                Action=[
                    awacs.apigateway.DELETE,
                    awacs.apigateway.GET,
                    awacs.apigateway.PATCH,
                    awacs.apigateway.POST,
                    awacs.apigateway.PUT
                ],
                Resource=[
                    APIGW_ARN('{0}-{1}'.format(
                        self.app_name,
                        self.stage_name)),
                    "arn:aws:apigateway:{aws_region_name}::/restapis/*".format(aws_region_name=self.aws_region_name),
                    "arn:aws:apigateway:{aws_region_name}::/restapis".format(aws_region_name=self.aws_region_name)
                ]
            ),

        ]

    def create_iam_policy(self):
        return [
            Statement(

                Effect=Allow,
                Action=[
                    awacs.iam.GetRole,
                    awacs.iam.PassRole,
                    awacs.iam.PutRolePolicy,
                ],
                Resource=[
                    '*'
                ]
            ),
            Statement(

                Effect=Allow,
                Action=[
                    awacs.iam.PassRole
                ],
                Resource=[
                    IAM_ARN('role/Zappa')
                ]
            )
        ]

    def create_lambda_policy(self):
        return [
            Statement(
                Effect=Allow,
                Action=[
                    awacs.awslambda.AddPermission,
                    awacs.awslambda.DeleteFunction,
                    awacs.awslambda.GetFunction,
                    awacs.awslambda.GetPolicy,
                    awacs.awslambda.ListVersionsByFunction,
                    awacs.awslambda.UpdateFunctionCode,
                    awacs.awslambda.RemovePermission

                ],
                Resource=[
                    LAMBDA_ARN('{0}-{1}'.format(
                        self.app_name, self.stage_name),region=self.aws_region_name,account='*')
                ]

            ),
            Statement(
                Effect=Allow,
                Action=[
                    awacs.awslambda.CreateFunction,
                ],
                Resource=[
                    '*'
                ]

            ),
        ]

    def create_events_policy(self):
        return [
            Statement(
                Effect=Allow,
                Action=[
                    awacs.events.ListRules,
                ],
                Resource=[
                    EVENTS_ARN('rule/*',region=self.aws_region_name, account='*')
                ]
            ),
            Statement(
                Effect=Allow,
                Action=[
                    awacs.events.PutRule,
                    awacs.events.PutTargets,
                    awacs.events.ListTargetsByRule,
                    awacs.events.DeleteRule,
                    awacs.events.RemoveTargets
                ],
                Resource=[
                    EVENTS_ARN(
                        resource='rule/{app_name}-{stage_name}-zappa-keep-warm-handler.keep_warm_callback'.format(
                            app_name=self.app_name,stage_name=self.stage_name),
                        region=self.aws_region_name, account='*')
                ]
            )
        ]