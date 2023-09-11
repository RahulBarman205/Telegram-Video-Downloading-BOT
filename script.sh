#!/bin/bash
monitor_terminal() {
	while true; do
		current_output=$(cat)

		if [ "$current_output" != "$previous_output" ]; then
			kill $python_pid
			break
		fi
previous_output="$current_output"
	done
}

python meow.py &
python_pid=$!

monitor_terminal &

wait

python telegram_youtube_downloader -k 6565741324:AAHn4lF4Ysx9AJYI2yfIscWhshzeov7DMZY