#!/bin/bash

# Ensure that a client list file is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <client_list_file>"
    exit 1
fi

client_file="$1"

# Ensure the logs directory exists
mkdir -p ./logs
output_csv="./logs/mminfo_output_$(date +%Y%m%d_%H%M%S).csv"

# Write CSV header
echo "Client,File Exists?,First Entry in servers file,mminfo Output (2nd line)" > "$output_csv"

# Use file descriptor 3 for reading input
exec 3< "$client_file"

while IFS= read -r raw_client <&3; do
    # Clean and ignore empty or commented lines
    raw_client=$(echo "$raw_client" | tr -d '\r' | xargs)
    [[ -z "$raw_client" || "$raw_client" =~ ^# ]] && continue

    # Remove the first occurrence of -nebr or -ebr from client name
    ssh_client=$(echo "$raw_client" | sed 's/-nebr//;s/-ebr//')

    file_exists="SSH Failed"
    first_entry="N/A"
    mminfo_output="N/A"

    # Check for /nsr/res/servers on remote host and get first line
    result=$(timeout 20s ssh -o BatchMode=yes \
                             -o StrictHostKeyChecking=no \
                             -o ConnectTimeout=10 \
                             -o LogLevel=ERROR \
                             "$ssh_client" \
                             'if [[ -f /nsr/res/servers ]]; then echo "Yes:$(head -n 1 /nsr/res/servers)"; else echo "No:"; fi' \
                             2>/dev/null)

    if [[ $? -eq 0 && -n "$result" ]]; then
        file_exists="${result%%:*}"
        first_entry="${result#*:}"
        [[ -z "$first_entry" ]] && first_entry="N/A"

        if [[ "$file_exists" == "Yes" && "$first_entry" != "N/A" ]]; then
            mminfo_output=$(timeout 20s ssh -o BatchMode=yes \
                                            -o StrictHostKeyChecking=no \
                                            -o ConnectTimeout=10 \
                                            -o LogLevel=ERROR \
                                            "$ssh_client" \
                                            "bash -lc \"mminfo -s '$first_entry' -avq 'client=$raw_client,savetime>1day ago' -ot | sed -n 2p\"" \
                                            2>/dev/null)
            [[ -z "$mminfo_output" ]] && mminfo_output="No output"
        else
            mminfo_output="Skipped"
        fi
    fi

    # Also print to console
    echo "$raw_client | $file_exists | $first_entry | $mminfo_output"

done

# Close file descriptor
exec 3<&-

echo "✅ All clients in the list have been processed"
