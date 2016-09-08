import click
import terminaltables
from zops import Zops

@click.group()
def zops():
    return

@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.option('--username',default=None,prompt='Username',help='Username for IAM user')
@click.option('--function_bucket',prompt='Function Bucket',help="Bucket for the function's code.")
@click.option('--static_bucket',prompt='Static Bucket',default=None,
              help='Bucket for your static assets.')
@click.option('--aws_region_name',prompt='AWS Region Name',
              default='us-east-1',help='AWS Region Name')
def create_user(app_name,stage_name,username,function_bucket,static_bucket,
                aws_region_name):
    z = Zops(app_name,stage_name,function_bucket=function_bucket,
                static_bucket=static_bucket,username=username,
                aws_region_name=aws_region_name)
    click.echo('Creating user: {0}'.format(username or zops.username))
    return z.create_user_stack()

@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
def user_credentials(app_name,stage_name):
    result = Zops(app_name,stage_name).user_stack_outputs()
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
def delete_user(app_name,stage_name):

    z = Zops(app_name,stage_name)
    z.delete_user_stack()
    click.echo('Deleted user stack: {0}'.format(z.user_stack_name), color="red")


@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.option('--function_bucket',prompt='Function Bucket',help="Bucket for the function's code.")
@click.option('--aws_region_name',prompt='AWS Region Name',default='us-east-1',help="AWS Region Name ")
def deploy_initial(app_name,stage_name,function_bucket,aws_region_name):
    z = Zops(app_name,stage_name,function_bucket=function_bucket,aws_region_name=aws_region_name)
    click.echo('Creating initial app...')
    z.create_initial_app()
    click.echo('Deploying initial app...')
    z.deploy_initial_app()
    click.echo('Deleting local copy of initial app...')
    z.delete_initial_app()

@zops.command()
@click.argument('app_name')
@click.argument('stage_name')
@click.option('--function_bucket',prompt='Function Bucket',help="Bucket for the function's code.")
@click.option('--aws_region_name',prompt='AWS Region Name',default='us-east-1',help="AWS Region Name ")
def undeploy_initial(app_name,stage_name,function_bucket,aws_region_name):
    z = Zops(app_name,stage_name,function_bucket=function_bucket,aws_region_name=aws_region_name)
    click.echo('Creating initial app...')
    z.create_initial_app()
    click.echo('Undeploying initial app...')
    z.undeploy_initial_app()
    click.echo('Deleting local copy of initial app...')
    z.delete_initial_app()


zops_ins = zops()