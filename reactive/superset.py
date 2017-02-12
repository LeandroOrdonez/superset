import subprocess
import pexpect
import os
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
#    subprocess.check_call(['pip','install', 'virtualenv'])
#    subprocess.check_call(['virtualenv', 'env'])
#    subprocess.check_call(['.', './venv/bin/activate'])
    hookenv.log('Installing Superset')
    subprocess.check_call(['pip','install', '--upgrade', 'setuptools', 'pip'])
    subprocess.check_call(['pip','install', 'superset'])
    set_state('superset.installed')

@when('superset.installed')
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
    child.send('admin')
    child.expect('\\r\\nUser first name \[admin\]: ')
    child.send('admin')
    child.expect('\\r\\nUser last name \[user\]: ')
    child.send('user')
    child.expect('\\r\\nEmail \[admin@fab.org\]: ')
    child.send('admin@fab.org')
    child.expect('\\r\\nPassword: ')
    child.send('admin')
    child.expect('\\r\\nRepeat for confirmation: ')
    child.send('admin')
    # Initialize the database
    hookenv.log('Initialize the database')
    subprocess.check_call(['superset','db', 'upgrade'])
    # Load some data to play with
    hookenv.log('Load some data to play with')
    subprocess.check_call(['superset', 'load_examples'])
    set_state('superset.configured')

@when('superset.configured')
def superset_startup():
    # Create default roles and permissions
    hookenv.log('Create default roles and permissions')
    subprocess.check_call(['superset', 'init'])
    # Start the web server on port 8088, use -p to bind to another port
    hookenv.log('Start the web server on port 8088')
    subprocess.check_call(['superset', 'runserver'])
    set_state('superset.running')
    status_set('ready', 'Superset up and running')
