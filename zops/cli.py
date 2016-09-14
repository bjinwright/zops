import click
import importlib
import terminaltables
from zops import Zops


@click.group()
@click.option('--profile_name',help='Credentials profile name. ',
              default='default')
@click.pass_context
def zops(ctx,profile_name):
    ctx.obj['profile_name'] = profile_name

@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.option('--username',default=None,prompt='Username',
              help='Username for IAM user')
@click.option('--function_bucket',prompt='Function Bucket',
              help="Bucket for the function's code.")
@click.option('--static_bucket',prompt='Static Bucket',default=None,
              help='Bucket for your static assets.')
@click.option('--aws_region_name',prompt='AWS Region Name',
              default='us-east-1',help='AWS Region Name')
@click.option('--user_temp_class',help='CloudFormation User Class',default='zops.user.UserTemplate')
@click.pass_context
def create_user(ctx,app_name,stage_name,username,function_bucket,static_bucket,
                aws_region_name,user_temp_class):
    z = Zops(app_name,stage_name,function_bucket=function_bucket,
                static_bucket=static_bucket,username=username,
                aws_region_name=aws_region_name,user_temp_class=user_temp_class,
             profile_name=ctx.obj['profile_name'])
    click.echo('Creating user: {0}'.format(username or zops.username))
    return z.create_user_stack()

@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.pass_context
def user_credentials(ctx,app_name,stage_name):
    result = Zops(app_name,stage_name,
                  profile_name=ctx.obj['profile_name']).user_stack_outputs()
    try:
        table_data = [
            [i['OutputKey'], i['OutputValue']]
            for i in result
            ]
    except TypeError:
        click.echo('User creds not ready yet.')
        return
    table_data.insert(0, ['Attribute','Value'])
    table = terminaltables.AsciiTable(table_data)
    click.echo(table.table)

@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.pass_context
def delete_user(ctx,app_name,stage_name):

    z = Zops(app_name,stage_name,profile_name=ctx.obj['profile_name'])
    z.delete_user_stack()
    click.echo('Deleted user stack: {0}'.format(z.user_stack_name),
               color="red")


@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.option('--function_bucket',prompt='Function Bucket',
              help="Bucket for the function's code.")
@click.option('--aws_region_name',prompt='AWS Region Name',
              default='us-east-1',help="AWS Region Name ")
@click.pass_context
def deploy_initial(ctx,app_name,stage_name,function_bucket,aws_region_name):
    z = Zops(app_name,stage_name,function_bucket=function_bucket,
             aws_region_name=aws_region_name,profile_name=ctx.obj['profile_name'])
    click.echo('Creating initial app...')
    z.create_initial_app()
    click.echo('Deploying initial app...')
    z.deploy_initial_app()
    click.echo('Deleting local copy of initial app...')
    z.delete_initial_app()

@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.option('--function_bucket',prompt='Function Bucket',
              help="Bucket for the function's code.")
@click.option('--aws_region_name',prompt='AWS Region Name',
              default='us-east-1',help="AWS Region Name ")
@click.pass_context
def undeploy_initial(ctx,app_name,stage_name,function_bucket,aws_region_name):
    z = Zops(app_name,stage_name,function_bucket=function_bucket,
             aws_region_name=aws_region_name,profile_name=ctx.obj['profile_name'])
    click.echo('Creating initial app...')
    z.create_initial_app()
    click.echo('Undeploying initial app...')
    z.undeploy_initial_app()
    click.echo('Deleting local copy of initial app...')
    z.delete_initial_app()

zops_ins = zops(obj={})