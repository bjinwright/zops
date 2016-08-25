import click


@click.group()
def zops():
    return

@zops.command()
@click.argument('username')
def create_user(username):
    click.echo(username)

if __name__ == '__main__':
    zops()