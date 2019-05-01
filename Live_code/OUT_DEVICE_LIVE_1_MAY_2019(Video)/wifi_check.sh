#!/bin/bash
ping -c 4 192.168.0.176
let a=$?
if [ "$a" = "0" ]; then
	echo "`date`, We have connection" >> $(echo $(pwd)/Test_Log/WifiNetLog.csv)
else
	echo "`date`, We have connection lost" >> $(echo $(pwd)/Test_Log/WifiNetLog.csv)
  #add command for reboot or restarting networking service here.
  #sudo ifconfig wlan0 down
  #sleep 5
  #sudo ifconfig wlan0 up
  break
fi
