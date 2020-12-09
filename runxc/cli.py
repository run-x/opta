import click
from PyInquirer import prompt, print_json
import sys
import pkg_resources

@click.command()
def main()-> int:
    """Microservice Generator"""
    print("Welcome to runxc. Please answer the following questions to generate your service.")

    questions = [
        {
            'type': 'input',
            'name': 'name',
            'message': 'Service name',
            'default': 'myservice'
        },
        {
            'type': 'list',
            'name': 'language',
            'message': 'Language',
            'choices': ['python'],
        },
        {
            'type': 'input',
            'name': 'outputDir',
            'message': 'Output directory',
            'default': lambda x: f"./{x['name']}"
        },
    ]

    answers = prompt(questions)
    print(answers['language'])
    print(answers['outputDir'])

    print(pkg_resources.resource_filename(__name__, 'templates/application/meow.py'))
    return 0

if __name__ == "__main__":
    main()
