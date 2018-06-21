#!/bin/bash

target_dir=$1
package_db_dir=$2
package_html_dir=$3

regex=".*/seqan3-library-([0-9]{8}).*"

latest_version=""

# Find all files with stable expression and sort them in decreasing order.
for f in $(find $target_dir -regextype sed -regex ".*/seqan3-library-[0-9]\{8\}\..*" | sort -r | head -n 1); do
    if [[ $f =~ $regex ]]
    then
        latest_version="${BASH_REMATCH[1]}"
        echo "Detected most recent version: ${latest_version}"
    else
        echo "No version found" # this could get noisy if there are a lot of non-matching files
        exit 128
    fi
done

if  [[ ! -z $latest_version ]]
then 
    for f in $(find $target_dir -regextype sed -regex ".*/seqan3-library-[0-9]\{8\}\..*" | sort -r); do
        if [[ $f =~ $regex ]]
        then
            version="${BASH_REMATCH[1]}"
            if [ "$version" != "$latest_version" ]
            then
                echo "Deleting file: ${f}"
                rm $f
            fi
        fi
    done
else
    echo "No stable nightly build detected!"
fi

# Update the package list
echo "Update package list."
base_dir=$(dirname "$0")
python ${base_dir}/packages.seqan.de/release_page.py -d $package_db_dir -o $package_html_dir
