#!/bin/bash
for filename in /Volumes/Backup\ Plus/stock/tsec/data/*.csv; do
    echo "$filename"
    tail -n 1230 "$filename" > "/Volumes/Backup Plus/stock/tsec/data/$(basename "$filename" .csv)_tmp.csv"
    mv "/Volumes/Backup Plus/stock/tsec/data/$(basename "$filename" .csv)_tmp.csv" "/Volumes/Backup Plus/stock/tsec/data/$(basename "$filename" .csv).csv"
done
