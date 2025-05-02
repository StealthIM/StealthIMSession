#!/bin/bash

tmux new-session -d -s stimenv 'cd ../StealthIMDB && make'
# tmux select-window -t stimenv:0
# tmux split-window -v 'cd ../StealthIMFileStorage && poetry run python main.py'
tmux attach-session -t stimenv