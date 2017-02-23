#!/bin/bash
#PYPID=$(ps | grep python | cut -b 2-7)
COUNT=0
ps | grep python | while read -r line; do
    PYPID=$(echo $line | cut -b 1-6)
    kill -s KILL $PYPID
    let COUNT=COUNT+1
done
echo "${COUNT} processes killed"
