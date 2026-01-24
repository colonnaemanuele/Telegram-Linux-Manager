#!/bin/sh

PARENT=$1
if [ -z "$PARENT" ]; then
  echo "Usage: $0 <parent_folder>"
  exit 1
fi

BASE=${PARENT%/*}
if [ "$BASE" = "$PARENT" ]; then
  BASE=$PARENT
fi

# Print used and total space for that filesystem
DISK_INFO=$(df -h "$BASE" | awk 'NR==2 {print $2, $3, $4, $5}')
TOTAL=$(echo "$DISK_INFO" | awk '{print $1}')
USED=$(echo "$DISK_INFO"  | awk '{print $2}')
FREE=$(echo "$DISK_INFO"  | awk '{print $3}')
PERC=$(echo "$DISK_INFO"  | awk '{print $4}')

echo "Used space in $BASE: $USED / $TOTAL ($PERC used, $FREE free)"

# Thresholds in KB
BLUE=15728640        # 15 GB
PURPLE=104857600     # 100 GB
YELLOW=367001600     # 350 GB
ORANGE=629145600     # 600 GB

# Collect folder sizes, sort descending, and print with colors
for FOLDER in "$PARENT"/*; do
  if [ -d "$FOLDER" ]; then
    SIZE_KB=$(du -sk "$FOLDER" 2>/dev/null | awk '{print $1}')
    echo "$SIZE_KB:$FOLDER"
  fi
done | sort -nr | while IFS=: read SIZE_KB FOLDER; do
  SIZE_HR=$(du -sh "$FOLDER" 2>/dev/null | awk '{print $1}')

  if [ "$SIZE_KB" -gt "$ORANGE" ]; then
    echo "\033[1;31m$FOLDER uses $SIZE_HR\033[0m"       # red (>600GB)
  elif [ "$SIZE_KB" -gt "$YELLOW" ]; then
      echo "\033[38;5;208m$FOLDER uses $SIZE_HR\033[0m"    # orange (351–600GB)
  elif [ "$SIZE_KB" -gt "$PURPLE" ]; then
      echo "\033[1;33m$FOLDER uses $SIZE_HR\033[0m"        # yellow (101–350GB)
  elif [ "$SIZE_KB" -gt "$BLUE" ]; then
      echo "\033[1;35m$FOLDER uses $SIZE_HR\033[0m"        # purple (15–100GB)
  else
      echo "\033[1;34m$FOLDER uses $SIZE_HR\033[0m"        # blue (<15GB)
  fi
done
