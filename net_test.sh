#!/bin/bash
while true
do
ping -c 4 192.168.0.172 
let a=$?
if [ "$a" = "0" ]; then
  echo "We have connection."
  break
else
  echo "We have lost connection.."
  #add command for reboot or restarting networking service here.
  sudo ifconfig wlan0 down
  sleep 5
  sudo ifconfig wlan0 up
fi
done
