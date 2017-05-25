index=1
for web_server_address in $(echo $web_server_addresses | tr "," "\n")
do
  sudo echo "	server my_app$index $web_server_address:8000 check" >> /etc/haproxy/haproxy.cfg
  index=$(($index+1))
done