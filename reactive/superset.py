import subprocess
import pexpect
import os
import sys
from charms.reactive import when, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import status_set
import charms.apt

@when_not('superset.installed')
def setup():
    hookenv.log('Installing dependencies for Superset')
    charms.apt.queue_install(['build-essential', 'libssl-dev', 'libffi-dev', 'python-dev', 'python-pip', 'libsasl2-dev', 'libldap2-dev'])
    charms.apt.install_queued()
    status_set('maintenance', 'Installing dependencies for superset')

@when_not('superset.installed')
@when('apt.installed.build-essential',
      'apt.installed.libssl-dev',
      'apt.installed.libffi-dev',
      'apt.installed.python-dev',
      'apt.installed.python-pip',
      'apt.installed.libsasl2-dev',
      'apt.installed.libldap2-dev')
def install_superset():
    status_set('maintenance', 'Installing superset')
    #init_virtualenv()
    hookenv.log('Installing Superset')
    subprocess.check_call(['pip','install', '--upgrade', 'setuptools', 'pip'])
    subprocess.check_call(['pip','install', 'superset'])
    set_state('superset.installed')

    hookenv.log('Switching to user ubuntu')
    subprocess.check_call(['su', '-', 'ubuntu'])
    hookenv.log('whoami: %s' % subprocess.check_output(['whoami']).strip())
    hookenv.log('cwd: %s' % os.getcwd())

@when('superset.installed')
@when_not('superset.configured')
def superset_setup():
    status_set('maintenance', 'Configuring superset')
    # Setting LC_ALL and LANG vbles
    os.environ['LC_ALL'] = 'C.UTF-8'
    os.environ['LANG'] = 'C.UTF-8'
    # Create an admin user (you will be prompted to set username, first and last name before setting a password)
    # Username [admin]:
    # User first name [admin]:
    # User last name [user]:
    # Email [admin@fab.org]:
    # Password:
    # Repeat for confirmation:
    hookenv.log('Creating admin user for Superset')
    child = pexpect.spawn('fabmanager create-admin --app superset')
    child.expect('\\r\\nUsername \[admin\]: ')
    child.sendline('admin')
    child.expect('\\r\\nUser first name \[admin\]: ')
    child.sendline('admin')
    child.expect('\\r\\nUser last name \[user\]: ')
    child.sendline('user')
    child.expect('\\r\\nEmail \[admin@fab.org\]: ')
    child.sendline('admin@fab.org')
    child.expect('\\r\\nPassword: ')
    child.sendline('admin')
    child.expect('\\r\\nRepeat for confirmation: ')
    child.sendline('admin')
    # Initialize the database
    hookenv.log('Initialize the database')
    subprocess.check_call(['superset','db', 'upgrade'])
    # Load some data to play with
    hookenv.log('Load some data to play with')
    subprocess.check_call(['superset', 'load_examples'])
    set_state('superset.configured')

@when('superset.installed',
      'superset.configured')
@when_not('superset.ready')
def superset_startup():
    # Create default roles and permissions
    hookenv.log('Create default roles and permissions')
    subprocess.check_call(['superset', 'init'])
    # Start the web server on port 8088, use -p to bind to another port
    #hookenv.log('Start the web server on port 8088')
    #subprocess.check_call(['superset', 'runserver'])
    set_state('superset.ready')
    status_set('active', 'Superset up and running')

def init_virtualenv():
    venv = os.path.abspath('./venv')
    hookenv.log('Virtualenv path: %s' % venv)
    vbin = os.path.join(venv, 'bin')
    vpip = os.path.join(vbin, 'pip')
    vpy = os.path.join(vbin, 'python')

    hookenv.log('Installing virtualenv')
    subprocess.check_call(['pip','install', 'virtualenv'])

    hookenv.log('Switching to user ubuntu')
    subprocess.check_call(['su', '-', 'ubuntu'])

    hookenv.log('Creating a virtualenv in %s' % venv)
    subprocess.check_call(['virtualenv', '--python=python3', 'venv'])

    hookenv.log('Activating venv')
    os.environ['PATH'] = ':'.join([vbin, os.environ['PATH']])
    reload_interpreter(vpy)


def reload_interpreter(python):
    """
    Reload the python interpreter to ensure that all deps are available.
    Newly installed modules in namespace packages sometimes seemt to
    not be picked up by Python 3.
    """
    os.execle(python, python, sys.argv[0], os.environ)
