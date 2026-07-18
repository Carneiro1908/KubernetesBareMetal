This code is to configure the k3s in the target VM, it always(ALWAYS), must be ran by the workflow, for security reasons
otherwise it wont access the secrets, and wont be able to work with VM.