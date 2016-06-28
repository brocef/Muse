#!/bin/bash
PYPID=$(ps | grep python | cut -b 2-7)
if [ ! $PYPID = "" ]
then
kill -s KILL $PYPID
fi
