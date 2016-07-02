#!/bin/bash

COUNT=0
for i in *.mp3; do
    rm "${i}"
    let COUNT=COUNT+1
done
for i in *.part; do
    rm "${i}"
    let COUNT=COUNT+1
done
for i in _v*.mp4; do
    rm "${i}"
    let COUNT=COUNT+1
done
echo "Removed ${COUNT} files"
