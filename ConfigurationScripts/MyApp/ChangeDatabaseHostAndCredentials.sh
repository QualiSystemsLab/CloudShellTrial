sudo sed -i -e "s/database_host: 127.0.0.1/database_host: $database_server_address/g" /acme/app/config/parameters.yml >null
sudo sed -i -e "s/background-color: #f9fAfb; }/background-color: #$app_color; }/g" /acme/web/assets/shop/css/style.css
