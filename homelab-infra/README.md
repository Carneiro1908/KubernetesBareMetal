This code is to configure the k3s in the target VM, it always(ALWAYS), must be ran by the workflow, for security reasons
otherwise it wont access the secrets, and wont be able to work with VM.

And for the workflow works normaly, you must have an already configured SSH key on the target VM

I am using a self-hosted workflow because it is more practical to access my LAN, however, depending of your 
goal/environment, adapt it for your needs

The grafana data is avaible in http://localhost:30300 of the VM, user is "admin" and the password is the one grafana_password("mypassword123")