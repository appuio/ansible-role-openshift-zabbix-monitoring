#     ___ ___ _  _ ___ ___    _ _____ ___ ___         
#    / __| __| \| | __| _ \  /_\_   _| __|   \        
#   | (_ | _|| .` | _||   / / _ \| | | _|| |) |       
#    \___|___|_|\_|___|_|_\/_/_\_\_|_|___|___/_ _____ 
#   |   \ / _ \  | \| |/ _ \_   _| | __|   \_ _|_   _|
#   | |) | (_) | | .` | (_) || |   | _|| |) | |  | |  
#   |___/ \___/  |_|\_|\___/ |_|   |___|___/___| |_|  
# 

# Example docker run command
# docker run -p 10050:10050 -p 10051:10051 -p 80:80 -p 443:443 oso-rhel7-zaio
# /usr/local/bin/start.sh will then start the mysqldb, zabbix, and httpd services.
# Default login:password to Zabbix is Admin:zabbix

FROM oso-rhel7-ops-base:latest

# Pause indefinitely if asked to do so.
ARG OO_PAUSE_ON_BUILD
RUN test "$OO_PAUSE_ON_BUILD" = "true" && while sleep 10; do true; done || :

ADD zabbix.repo /etc/yum.repos.d/

# Install zabbix (and supporting tools) from zabbix repo

# By default docker recommends to install packages with tsflags=nodocs for space saving
# but in this case, we need it for this one package, because the DB schema is coming from the docs
RUN yum-install-check.sh -y --setopt=tsflags='' zabbix-server-mysql
RUN yum-install-check.sh -y mod_ssl zabbix-sender zabbix-agent \
    zabbix-web-mysql mariadb mariadb-server openssh-clients openshift-tools-scripts-monitoring-zabbix-heal && \
    yum -y update && \
    yum clean all

ADD root/ /root/

# Add mysql files
ADD mariadb-prepare-db-dir /usr/libexec/
ADD my.cnf /etc/

# Add zabbix mysql files
ADD zabbix/db_create/createdb.sh /root/
ADD zabbix/db_create/create_zabbix.sql /root/

# Lay down zabbix conf
ADD zabbix/conf/zabbix_server.conf /etc/zabbix/
ADD zabbix/conf/zabbix_agentd.conf /etc/zabbix/
ADD zabbix/conf/zabbix_agent.conf /etc/zabbix/

# Set the timezone in the php.ini file
RUN sed -r -i -e 's/^;(date.timezone).*/\1 = America\/New_York/g' /etc/php.ini

# Zabbix web
ADD zabbix/conf/zabbix.conf.php /etc/zabbix/web/

# Rhel 7.2 update
ADD httpd.conf /etc/httpd/conf/
RUN sed -i -e 's/^\(LoadModule auth_digest_module modules\/mod_auth_digest.so\)$/#\1/g' /etc/httpd/conf.modules.d/00-base.conf

# adding redirect to the main apache config, so it will send every request to the /zabbix folder
ADD welcome.conf /etc/httpd/conf.d/

# Start mysqld, zabbix, and apache
ADD start.sh /usr/local/bin/
CMD /usr/local/bin/start.sh
