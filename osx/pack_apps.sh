#!/bin/bash

source_dir=$1
build_dir=$2
arch_sse4=$3
arch_avx2=$4
user="user"
remote="larix.imp.fu-berlin.de"
remote_dir="/web/packages.seqan.de/htdocs"
target_dir="$user@$remote:$remote_dir"

echo "SOURCE_DIR = ${source_dir}"
echo "BUILD_DIR = ${build_dir}"

wd=$(pwd)
target_dir="$wd/bin" 
cd "$source_dir/apps"
apps_dir=$(pwd)
abs_src_dir="$(dirname $apps_dir)"
echo "SOURCE_DIR=$abs_src_dir"
echo "TARGET_DIR=$target_dir"
apps=()
for app in *;
do
  if [[ -d $app ]]; then
    apps+=("$app")
  fi
done

cd "$wd"
cd "$build_dir"

for app in "${apps[@]}"
do
  # Call cmake for the app
  echo "Packaging $app"
  rm -rf *
  echo "cmake $abs_src_dir -DCMAKE_CXX_COMPILER=clang++-mp-6 -DSEQAN_BUILD_SYSTEM=APP:$app -DSEQAN_STATIC_APPS=1 -DSEQAN_ARCH_SSE4=${arch_sse4} -DSEQAN_ARCH_AVX2=${arch_avx2}"
  cmake $abs_src_dir -DCMAKE_CXX_COMPILER=clang++-mp-3.9 -DSEQAN_BUILD_SYSTEM=APP:$app -DSEQAN_STATIC_APPS=1 -DSEQAN_ARCH_SSE4="${arch_sse4}" -DSEQAN_ARCH_AVX2="${arch_avx2}"
  if [ -f "Makefile" ] 
  then
    make package -j 4
    echo "mv $app* $target_dir"
    mkdir -p "$target_dir/$app"
    mv "$app"* "$target_dir/$app" 
    #rsync -az "$app"* "$target_dir/$app"
  fi
done
