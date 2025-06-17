#!/bin/bash

# Function to print a modern progress bar
progress_bar() {
    local progress=$1
    local width=50
    local filled=$((progress * width / 100))
    local empty=$((width - filled))
    local bar=""

    for ((i=0; i<filled; i++)); do bar+="#"; done
    for ((i=0; i<empty; i++)); do bar+=" "; done

    echo -ne "\r[${bar}] $progress%"
}

# Automatically detect latest uploaded file for this session
SESSION_ID=$(basename "$(ls -t uploads/*.txt 2>/dev/null | head -n1)" | cut -d_ -f1)

# Validate
if [ -z "$SESSION_ID" ]; then
    echo "Error: Unable to detect session ID from uploads."
    exit 1
fi

FILE=$(ls -t uploads/"${SESSION_ID}"_*.txt 2>/dev/null | head -n1)

if [ ! -f "$FILE" ]; then
    echo "Error: No input file found for session ID $SESSION_ID"
    exit 1
fi

# Count total lines
total_steps=$(wc -l < "$FILE")
current_step=0
result_file=$(mktemp)

# --- Disabling policies ---
echo -e "\nDisabling policies..."

exec 3< "$FILE"
while read -r line <&3; do
    master=$(echo "$line" | awk '{print $2}')
    policy=$(echo "$line" | awk '{print $3}')
    cr=$(echo "$line" | awk '{print $4}')

    cmd="sudo /usr/openv/netbackup/bin/admincmd/bpplinfo $policy -modify -inactive -keyword 'Migrated to Networker as per $cr' -M $master"
    ssh -tt -o StrictHostKeyChecking=no "$master" "$cmd" < /dev/null > /dev/null 2>&1

    current_step=$((current_step + 1))
    progress=$((current_step * 100 / total_steps))
    progress_bar $progress
    sleep 0.2
done
exec 3<&-

echo -e "\nPolicy disabling completed."

# --- Validating policies ---
echo -e "\nValidating policies..."
current_step=0

exec 3< "$FILE"
while read -r line <&3; do
    master=$(echo "$line" | awk '{print $2}')
    policy=$(echo "$line" | awk '{print $3}')

    output=$(ssh -tt -o StrictHostKeyChecking=no "$master" "sudo /opt/openv/netbackup/bin/admincmd/bpplinfo $policy -L | grep 'Active'" < /dev/null 2>/dev/null)
    echo "Policy: $policy - ${output:-No Active status found} on $master" >> "$result_file"

    current_step=$((current_step + 1))
    progress=$((current_step * 100 / total_steps))
    progress_bar $progress
    sleep 0.2
done
exec 3<&-

# --- Final Output ---
echo -e "\nPolicy validation completed."
echo -e "\nScript execution completed successfully!"
echo -e "\nConsolidated Policy Validation Results:"
cat "$result_file"
rm "$result_file"

