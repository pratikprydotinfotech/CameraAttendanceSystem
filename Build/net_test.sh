#!/bin/bash
var1="We have connection Lost"
var2="We have connection"

"Internet_Connectivity_Test" > InternetStatus.txt 
while true
do
ping -c 4 192.168.0.172 
let a=$?
if [ "$a" = "0" ]; then
  echo "We have connection." >> InternetStatus.txt
else
  echo "We have lost connection.." >> InternetStatus.txt
  #add command for reboot or restarting networking service here.
  #sudo ifconfig wlan0 down
  #sleep 5
  #sudo ifconfig wlan0 up
  break
fi
done
