#!/bin/bash

file="/app/target_file.txt"
output_file="/tmp/line_output.txt"
email_recipient="phani051@gmail.com"
email_subject="Contents of target_file.txt from $(hostname)"

if [[ -f "$file" ]]; then
    echo "Printing each line separately from $file:" | tee "$output_file"
    line_number=1
    while IFS= read -r line; do
        {
            echo "---------------------"
            echo "Line $line_number:"
            echo "$line"
        } | tee -a "$output_file"
        ((line_number++))
    done < "$file"
    echo "---------------------" | tee -a "$output_file"

else
    echo "File $file does not exist."
fi