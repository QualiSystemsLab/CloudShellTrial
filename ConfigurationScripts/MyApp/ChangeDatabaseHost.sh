sudo sed -i -e "s/database_host: 127.0.0.1/database_host: $database_server_address/g" /acme/app/config/parameters.yml
ip="$(ifconfig | grep -A 1 'eth0' | tail -1 | cut -d ':' -f 2 | cut -d ' ' -f 1)"
sudo pkill php
sleep 5s
sudo php /acme/bin/console server:start $ip:8000 --force
