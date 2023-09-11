@echo off 
 
python "meow.py" 
SET "python_pid=%!%" 
CALL :monitor_terminal 
wait 
python "telegram_youtube_downloader" "-k" "6565741324:AAHn4lF4Ysx9AJYI2yfIscWhshzeov7DMZY" 
 
EXIT /B %ERRORLEVEL% 
 
:monitor_terminal 
REM UNKNOWN: {"type":"While","clause":{"type":"CompoundList","commands":[{"type":"Command","name":{"text":"true","type":"Word"}}]},"do":{"type":"CompoundList","commands":[{"type":"Command","prefix":[{"text":"current_output=$(cat)","expansion":[{"loc":{"start":15,"end":20},"command":"cat","type":"CommandExpansion","commandAST":{"type":"Script","commands":[{"type":"Command","name":{"text":"cat","type":"Word"}}]}}],"type":"AssignmentWord"}]},{"type":"If","clause":{"type":"CompoundList","commands":[{"type":"Command","name":{"text":"[","type":"Word"},"suffix":[{"text":"\"$current_output\"","expansion":[{"loc":{"start":1,"end":15},"parameter":"current_output","type":"ParameterExpansion"}],"type":"Word"},{"text":"!=","type":"Word"},{"text":"\"$previous_output\"","expansion":[{"loc":{"start":1,"end":16},"parameter":"previous_output","type":"ParameterExpansion"}],"type":"Word"},{"text":"]","type":"Word"}]}]},"then":{"type":"CompoundList","commands":[{"type":"Command","name":{"text":"kill","type":"Word"},"suffix":[{"text":"$python_pid","expansion":[{"loc":{"start":0,"end":10},"parameter":"python_pid","type":"ParameterExpansion"}],"type":"Word"}]},{"type":"Command","name":{"text":"break","type":"Word"}}]}},{"type":"Command","prefix":[{"text":"previous_output=\"$current_output\"","expansion":[{"loc":{"start":17,"end":31},"parameter":"current_output","type":"ParameterExpansion"}],"type":"AssignmentWord"}]}]}} 
EXIT /B 0