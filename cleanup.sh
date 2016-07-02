#!/bin/bash

COUNT=0
for i in *.mp3; do
    if [ $i != "*.mp3" ]
    then
        rm "${i}"
        let COUNT=COUNT+1
    fi
done
for i in *.part; do
    if [ $i != "*.part" ]
    then
        rm "${i}"
        let COUNT=COUNT+1
    fi
done
for i in _v*.mp4; do
    if [ $i != "_v*.mp4" ]
    then
        rm "${i}"
        let COUNT=COUNT+1
    fi
done
echo "Removed ${COUNT} files"
