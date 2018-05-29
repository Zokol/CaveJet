#!/bin/bash
cd /home/pi/CaveJet
while :
do
	git pull
	python cavejet.py
done
