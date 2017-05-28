sudo sed -i -e "s/database_host: 127.0.0.1/database_host: $database_server_address/g" /acme/app/config/parameters.yml
reboot
