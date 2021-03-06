#!/bin/bash

# This script is for configuration paths.
#
# Testet with ubuntu-server 14.04 and 16.04 in 2016
#
# Dieses kleine Script uebernimmt die Configuration
# der Pfade fuer Admin-SRB auf dem Server
# 
# Author: Joerg Sorge
# Distributed under the terms of GNU GPL version 2 or later
# Copyright (C) Joerg Sorge joergsorge@gmail.com
# 2016-11-29
#
echo ""
echo "Admin-SRB Data Path Configuration..."
echo "Use this script only for a fresh install!"
echo "Run this script not with sudo!"
echo "Main path must exist (mount point of data hd)"
echo "It provides following steps:"
echo "- Set permissions for main path"
echo "- Making sub paths"

echo ""
read -p "Are you sure to config file-paths? (y/n) " -n 1
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
	echo ""
	echo "Configuration aborted"
	exit
fi

echo "The standard path is: /mnt/data_server"
echo "Leave the input blank if you using this path"
echo "Otherwise type in a new path"
echo ""
read -p 'input data path for media files: ' path_media
if [ -z "$path_media" ]; then
  path_media=/mnt/data_server
fi

echo "Set permissions..."
sudo chmod o+rwx $path_media
sudo chgrp users $path_media
sudo chmod g+sw $path_media
sudo chown $USER $path_media

echo "Making sub paths..."
mkdir $path_media/Play_Out_Archiv
mkdir $path_media/Play_Out_Archiv/Archiv_HF_Infotime
mkdir $path_media/Play_Out_Archiv/Archiv_HF_Sendung
mkdir $path_media/Play_Out_Server
mkdir $path_media/Play_Out_Server/Play_Out_Infotime
mkdir $path_media/Play_Out_Server/Play_Out_Layout
mkdir $path_media/Play_Out_Server/Play_Out_Rotation
mkdir $path_media/Play_Out_Server/Play_Out_Sendung

echo "Making media path for samba/fstab access..."
mkdir "$(pwd)"/srb-net
mkdir "$(pwd)"/srb-net/play_out_server

echo ""
echo "Congratiulations!"
echo "Now you can take off your shoes and sitting down in a chair..."
echo "...finish"
echo ""
exit
