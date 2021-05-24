$ git clone <Project A>  # Cloning project repository
$ cd <Project A> # Enter to project directory
$ sudo ython3 -m venv my_venv # If not created, creating virtualenv, in WSL important
$ source ./my_venv/bin/activate # Activating virtualenv
(my_venv)$ pip3 install -r ./requirements.txt # Installing dependencies
(my_venv)$ deactivate # When you want to leave virtual environment
