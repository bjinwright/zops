import click
import terminaltables
from zops import Zops

@click.group()
@click.argument('app_name')
@click.argument('stage_name')
@click.pass_context
def zops(ctx,app_name,stage_name):
    ctx.obj['app_name'] = app_name
    ctx.obj['stage_name'] = stage_name
    ctx.obj['zops'] = Zops(app_name,stage_name)

@zops.command()
@click.pass_context
@click.option('--username',default=None)
@click.option('--function_bucket',prompt='Function Bucket',help="Bucket for the function's code.")
@click.option('--static_bucket',prompt='Static Bucket',help='Bucket for your static assets.')
def create_user(ctx,username,function_bucket,static_bucket):
    click.echo('Creating user: {0}'.format(username or ctx.obj['zops'].username))
    return ctx.obj['zops'].create_user_stack(username,function_bucket,static_bucket)

@zops.command()
@click.pass_context
@click.option('--username',prompt='Username?')
def user_credentials(ctx,username):
    result = ctx.obj['zops'].user_stack_outputs(username)
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
@click.option('--function_bucket',prompt='Function Bucket',help="Bucket for the function's code.")
@click.pass_context
def deploy_initial(ctx,function_bucket):
    click.echo('Creating initial app...')
    ctx.obj['zops'].create_initial_app(function_bucket)
    click.echo('Deploying initial app...')
    ctx.obj['zops'].deploy_initial_app()
    click.echo('Deleting local copy of initial app...')
    ctx.obj['zops'].delete_initial_app()


zops_ins = zops(obj={})