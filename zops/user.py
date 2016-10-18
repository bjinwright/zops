import awacs
import re
import string
import awacs.cloudformation

from awacs.apigateway import ARN as APIGW_ARN
from awacs.aws import Allow, Policy, Statement
from awacs.awslambda import ARN as LAMBDA_ARN
from awacs.iam import ARN as IAM_ARN
from awacs.s3 import ARN as S3_ARN
from awacs.events import ARN as EVENTS_ARN
from awacs.cloudformation import ARN as CLOUDFORMATION_ARN
from troposphere import GetAtt, Output, Ref, Template
from troposphere.iam import PolicyType, User, AccessKey


alpha_num_pattern = re.compile('[\W_]+')



class UserTemplate(object):

    def render(self,app_name=None,stage_name=None,username=None,function_bucket=None,
                 static_bucket=None,aws_region_name='us-east-1'):
        self.app_name = app_name
        self.stage_name = stage_name
        self.username = username
        self.function_bucket = function_bucket
        self.static_bucket = static_bucket
        self.aws_region_name = aws_region_name
        self.t = Template()
        self.t.add_description(
            "Zappa Template for {app_name}-{stage_name} ".format(
                app_name=self.app_name, stage_name=self.stage_name))

        zappa_user = self.t.add_resource(User(self.username))
        zappa_user_keys = self.t.add_resource(AccessKey(
            "ZappaUserKeys",
            Status="Active",
            UserName=Ref(zappa_user))
        )
        self.t.add_resource(
            PolicyType(
                alpha_num_pattern.sub('',"{app_name}{stage_name}".format(
                    app_name=self.app_name,
                    stage_name=self.stage_name)),
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

    def get_statement_list(self):
        stm_list = []
        stm_list.extend(self.create_s3_policy())
        stm_list.extend(self.create_iam_policy())
        stm_list.extend(self.create_apigw_policy())
        stm_list.extend(self.create_lambda_policy())
        stm_list.extend(self.create_events_policy())
        stm_list.extend(self.create_cloudformation_policy())
        return stm_list

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
                    awacs.awslambda.RemovePermission,
                    awacs.awslambda.UpdateFunctionConfiguration

                ],
                Resource=[
                    LAMBDA_ARN('{0}-{1}'.format(
                        self.app_name, self.stage_name), region=self.aws_region_name, account='*')
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

    def create_cloudformation_policy(self):
        return [
            Statement(
                Effect=Allow,
                Action=[
                    awacs.cloudformation.Action('*')
                ],
                Resource=[
                    CLOUDFORMATION_ARN(
                        resource='*',
                        region=self.aws_region_name,
                        account='*'
                    )
                ]
            )
        ]
    def create_events_policy(self):
        return [
            Statement(
                Effect=Allow,
                Action=[
                    awacs.events.ListRules,
                ],
                Resource=[
                    EVENTS_ARN('rule/*', region=self.aws_region_name, account='*')
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
                            app_name=self.app_name, stage_name=self.stage_name),
                        region=self.aws_region_name, account='*')
                ]
            )
        ]