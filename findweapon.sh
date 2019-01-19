#!/bin/bash

if [ -z "$1" ]; then
    read -p "Weapon Name: " name
else
    name="$1"
fi
grep _Name "$HOME/.steam/steam/steamapps/common/Into the Breach/scripts/text_weapons.lua" | grep -i "$name" | rev | cut -d _ -f 2- | rev
