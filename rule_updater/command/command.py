import click

@click.command()
#@click.option('--target', default=1, help='Number of greetings.')
#@click.option('--name', prompt='your name', help='The person to greet.')
@click.option('--name', prompt='your name', help='The person to greet.')
def command_start(count, name):
   print(count, name)


if __name__ == '__main__':
    command_start()

