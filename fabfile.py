import glob
import os
from subprocess import check_call
import sys
import json

from fabric.api import cd, env, prefix, run, sudo
from fabric.contrib import files
from fabric.operations import put

DEPLOYMENTS = {}

deployments_file = os.environ.get('DEPLOYMENTS_JSON', 'deployments.json')
if os.path.exists(deployments_file):
    with open(deployments_file, 'r') as f:
        imported_deployments = json.load(f)
        DEPLOYMENTS.update(imported_deployments)

def kobo_workon(_virtualenv_name):
    return prefix('kobo_workon %s' % _virtualenv_name)


def exit_with_error(message):
    print message
    sys.exit(1)


def check_key_filename(deployment_configs):
    if 'key_filename' in deployment_configs and \
       not os.path.exists(deployment_configs['key_filename']):
        # Maybe the path contains a ~; try expanding that before failing
        deployment_configs['key_filename'] = os.path.expanduser(
            deployment_configs['key_filename']
        )
        if not os.path.exists(deployment_configs['key_filename']):
            exit_with_error("Cannot find required permissions file: %s" %
                            deployment_configs['key_filename'])


def setup_env(deployment_name):
    deployment = DEPLOYMENTS.get(deployment_name)


    if deployment is None:
        exit_with_error('Deployment "%s" not found.' % deployment_name)

    if 'kc_virtualenv_name' in deployment:
        deployment['virtualenv_name'] = deployment['kc_virtualenv_name']

    env.update(deployment)

    check_key_filename(deployment_name)

    env.virtualenv = os.path.join('/home', 'ubuntu', '.virtualenvs',
                                  env.kc_virtualenv_name, 'bin', 'activate')

    env.pip_requirements_file = os.path.join(env.kc_path,
                                             'requirements/base.pip')
    env.template_dir = 'onadata/libs/custom_template'
    env.template_repo = os.path.join(env.home, 'kobocat-template')


def deploy_template(env):
    if env.get('template'):
        run("mkdir -p %s" % env.template_repo)
        run("ls -al %s" % env.template_repo)
        run("rm -rf %s" % env.template_repo)
        if env.get('template_branch'):
            run("git clone -b %s %s %s" %
                (env.get('template_branch'), env.get('template'), env.template_repo))
        else:
            run("git clone %s %s" % (env.get('template'), env.template_repo))


def reload(deployment_name, branch='master'):
    setup_env(deployment_name)
    run("sudo restart celeryd")
    run("sudo restart uwsgi")


def deploy(deployment_name, branch='master'):
    setup_env(deployment_name)
    with cd(env.kc_path):
        run("git fetch origin")
        run("git checkout origin/%s" % branch)

        deploy_template(env)

        run('find . -name "*.pyc" -exec rm -rf {} \;')
        run('find . -type d -empty -delete')

    # numpy pip install from requirements file fails
    with kobo_workon(env.kc_virtualenv_name):
        run("pip install numpy")
        run("pip install -r %s" % env.pip_requirements_file)

    with cd(env.kc_path):
        with kobo_workon(env.kc_virtualenv_name):
            run("python manage.py syncdb --all")
            run("python manage.py migrate")
            run("python manage.py collectstatic --noinput")

    run("sudo restart celeryd")
    run("sudo restart uwsgi")
