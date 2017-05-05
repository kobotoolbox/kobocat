import json
import os
import sys

from fabric.api import cd, env, prefix, run


DEPLOYMENTS = {}

deployments_file = os.environ.get('DEPLOYMENTS_JSON', 'deployments.json')
if os.path.exists(deployments_file):
    with open(deployments_file, 'r') as f:
        imported_deployments = json.load(f)
        DEPLOYMENTS.update(imported_deployments)


def run_no_pty(*args, **kwargs):
    # Avoids control characters being returned in the output
    kwargs['pty'] = False
    return run(*args, **kwargs)


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
            exit_with_error("Cannot find required SSH key file: %s" %
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
    run("sudo restart kc_celeryd")
    run("sudo restart uwsgi")


def deploy_ref(deployment_name, ref):
    setup_env(deployment_name)
    with cd(env.kc_path):
        run("git fetch --all --tags")
        # Make sure we're not moving to an older codebase
        git_output = run_no_pty(
            'git rev-list {}..HEAD --count 2>&1'.format(ref))
        if int(git_output) > 0:
            raise Exception("The server's HEAD is already in front of the "
                "commit to be deployed.")
        # We want to check out a specific commit, but this does leave the HEAD
        # detached. Perhaps consider using `git reset`.
        run('git checkout {}'.format(ref))
        # Report if the working directory is unclean.
        git_output = run_no_pty('git status --porcelain')
        if len(git_output):
            run('git status')
            print('WARNING: The working directory is unclean. See above.')

        deploy_template(env)

        run('find . -name "*.pyc" -exec rm -rf {} \;')
        run('find . -type d -empty -delete')

    # numpy pip install from requirements file fails
    with kobo_workon(env.kc_virtualenv_name):
        run("pip install numpy")
        run("pip install --upgrade -r %s" % env.pip_requirements_file)

    formpack_path = os.path.join(env.home, 'formpack')
    formpack_branch = env.get('formpack_branch', False)
    run("[ -d {fp} ] || git clone https://github.com/kobotoolbox/formpack.git "
        "{fp}".format(fp=formpack_path))

    with cd(formpack_path):
        with kobo_workon(env.kc_virtualenv_name):
            if formpack_branch:
                run("git checkout {b} && git pull origin {b}"
                    .format(b=formpack_branch))
            run("python setup.py develop")

    with cd(os.path.join(env.kc_path, "onadata", "static")):
        run("date > LAST_UPDATE.txt")

    with cd(env.kc_path):
        with kobo_workon(env.kc_virtualenv_name):
            run("python manage.py syncdb")
            run("python manage.py migrate")
            run("python manage.py collectstatic --noinput")

    run("sudo restart kc_celeryd")
    run("sudo restart uwsgi")


def deploy(deployment_name, branch='origin/master'):
    deploy_ref(deployment_name, branch)
