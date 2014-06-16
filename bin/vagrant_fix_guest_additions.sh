#!/bin/sh

vagrant plugin install vagrant-vbguest
vagrant up --no-provision
vagrant ssh -c 'sudo apt-get -y -q purge virtualbox-guest-dkms virtualbox-guest-utils virtualbox-guest-x11'
vagrant halt
vagrant up --provision
