# The following command calls nssm to change the argument of the SeleniumGridNode service. '' is used to mark the end of the variable name
nssm set SeleniumGridNode AppParameters -jar C:\selenium\selenium-server-standalone-3.4.0.jar -role node -hub http://$env:hub_server_address'':4444/grid/register
Restart-Service SeleniumGridNode
