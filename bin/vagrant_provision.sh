#!/bin/bash

# Shell script to provision the vagrant box.

# FIXME - add md5 check to see if this script has changed since the
# last time it was run and if not, have it exit.

set -e
set -x

cd ~vagrant/fjord

# Update sources and package indexes:
apt-get update

#configure locales:
export LC_ALL="en_US.UTF-8"
locale-gen en_US.UTF-8

# Install node and npm:
apt-get install -y -q npm
# Homogenize binary name with production RHEL:
ln -sf /usr/bin/nodejs /usr/local/bin/node

# Install node modules from package.json
sudo -H -u vagrant npm install

# Install Python development-related things:
apt-get install -y -q libapache2-mod-wsgi python-pip python-virtualenv libpython-dev
pip install nose Sphinx

# Install git:
apt-get install -y -q git

# Install MySQL:
# But first, we have to tell it to not prompt us about the password
# because we want it to be "password" and the prompt messes up the
# vagrant output.
debconf-set-selections <<< 'mysql-server mysql-server/root_password password password'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password password'
apt-get install -y -q mysql-client mysql-server libmysqlclient-dev

mysql -uroot -ppassword -hlocalhost \
    -e "CREATE DATABASE fjord CHARACTER SET utf8 COLLATE utf8_unicode_ci;"
mysql -uroot -ppassword -hlocalhost \
    -e "CREATE USER 'fjord'@'localhost' IDENTIFIED BY 'password';"
mysql -uroot -ppassword -hlocalhost \
    -e "GRANT ALL ON fjord.* TO 'fjord'@'localhost' IDENTIFIED BY 'password'"
mysql -uroot -ppassword -hlocalhost \
    -e "GRANT ALL ON test_fjord.* TO 'fjord'@'localhost' IDENTIFIED BY 'password'"

VENV=/home/vagrant/.virtualenvs/fjordvagrant

# Build virtual environment and activate it
sudo -H -u vagrant virtualenv $VENV

# Install bits we need for compiled requirements
apt-get install -y -q libxml2 libxml2-dev libxslt1.1 libxslt1-dev libyaml-dev

# Install Fjord requirements
sudo -H -u vagrant -s -- <<EOF
source $VENV/bin/activate
cd ~/fjord
./peep.sh install -r requirements/requirements.txt
./peep.sh install -r requirements/compiled.txt
./peep.sh install -r requirements/dev.txt
pre-commit install -f
EOF

# Install Elasticsearch 0.90.10
curl http://packages.elasticsearch.org/GPG-KEY-elasticsearch | apt-key add -
echo "deb http://packages.elasticsearch.org/elasticsearch/0.90/debian stable main" \
    > /etc/apt/sources.list.d/elasticsearch.list
apt-get update
apt-get install -y -q openjdk-7-jre-headless
apt-get install elasticsearch=0.90.10
update-rc.d elasticsearch defaults 95 10

# Install memcached
apt-get install -y -q memcached

# Install subversion (used to download locales)
apt-get install -y -q subversion

# Install gettext (used to compile locales)
apt-get install -y -q gettext

# Create local settings file if it doesn't exist
[ -f fjord/settings/local.py ] || cp fjord/settings/local.py-dist fjord/settings/local.py

# Remove unused packages, most of them are related to X server
# and we don't use X server at all.
apt-get autoremove -y -q

# Activate the virtual environment in .bashrc
echo ". $VENV/bin/activate" >> /home/vagrant/.bashrc

# Add the 'bin' folder of local node modules to $PATH
echo "export PATH=\$PATH:/home/vagrant/fjord/node_modules/.bin/" >> /home/vagrant/.bashrc

# FIXME: Change the motd file so that it has a link to Fjord docs,
# tells the user where the code is and lists common commands.

cat <<EOF

************************************************************************

If it gets here, then the Vagrant VM is provisioned. You should be all
set.

Consult the documentation on how to use and maintain this VM.

https://fjord.readthedocs.org/

Next steps:

1. hop on #input on irc.mozilla.org and say hi
2. find a bug to work on

************************************************************************

EOF
