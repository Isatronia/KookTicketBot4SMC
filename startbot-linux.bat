kill -SIGKILL $(pidof -s python3)
python3 bot.py 2>&1 | tee log/"$(date +"%Y-%m-%d")".log
