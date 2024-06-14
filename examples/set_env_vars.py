import json
import os
import platform

def set_env_vars_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
        
        env_vars = {}
        for service, creds in data.items():
            for key, value in creds.items():
                env_var = f"{service.upper()}_{key.upper()}"
                env_vars[env_var] = value
                print(f"Set {env_var} to {value}")
                os.environ[env_var] = value  # Set for the current session
                
        if platform.system() == 'Windows':
            set_env_vars_windows(env_vars)
        else:
            set_env_vars_unix(env_vars)

def set_env_vars_windows(env_vars):
    for var, value in env_vars.items():
        command = f'setx {var} "{value}"'
        os.system(command)
    print("Environment variables set permanently for Windows.")

def set_env_vars_unix(env_vars):
    shell = os.environ.get('SHELL', '/bin/bash')
    if 'bash' in shell:
        profile_path = os.path.expanduser('~/.bashrc')
    elif 'zsh' in shell:
        profile_path = os.path.expanduser('~/.zshrc')
    else:
        profile_path = os.path.expanduser('~/.profile')
    
    with open(profile_path, 'a') as profile:
        profile.write('\n# Environment variables set by script\n')
        for var, value in env_vars.items():
            profile.write(f'export {var}="{value}"\n')
    
    print(f"Environment variables set permanently in {profile_path}.")
    print("Please restart your terminal or run 'source ~/.bashrc' (or the relevant file) to apply the changes.")

if __name__ == "__main__":
    json_file = 'credentials.json'
    set_env_vars_from_json(json_file)
