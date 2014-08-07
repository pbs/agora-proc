#!/bin/bash
# Check for argument - must be the username to setup
if [ -z "$1" ]
    then
        echo "Usage: $0"
    exit
fi
##########################################
# Put all installation commands here
##########################################
# install http
# Already installed on this virtualbox
#sudo yum -y install httpd
# install memcached
#echo "===> Installing memcached"
#sudo yum -y install memcached
#
# Run a bunch of commands as the user
echo "===> Running scripts"
su $1 << 'SCRIPT'

SCRIPT
