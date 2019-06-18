sudo sed -i -e "s/database_host: 127.0.0.1/database_host: $database_server_address/g" /acme/app/config/parameters.yml >null
sudo sed -i -e "s/background-color: #f9fAfb; }/background-color: #$app_color; }/g" /acme/web/assets/shop/css/style.css
sudo sed -i -e "s/database_user: dbuser/database_user: $database_user/g" /acme/app/config/parameters.yml >null
sudo sed -i -e "s/database_password: i-00265dc25461c4061; }/background-color: #$database_password; }/g" /acme/web/assets/shop/css/style.css
