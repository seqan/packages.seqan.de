#!/bin/sh

SEQAN_SRC=$1
SEQAN_BUILDS=$2
MARCH=$3
SEQAN_PACKAGES="C:/seqan-release/package_db"

if [ $# -lt 2 ]
then
    echo "usage: $0 <seqan-src> <seqan-builds> [arch]"
    exit
fi

if [ -n "${MARCH}" ]
then
    FLAGS+=" -DSEQAN_SYSTEM_PROCESSOR=${MARCH}"
fi

if [ -n "${CC}" ]
then
    FLAGS+=" -DCMAKE_C_COMPILER=${CC}"
fi

if [ -n "${CXX}" ]
then
    FLAGS+=" -DCMAKE_CXX_COMPILER=${CXX}"
fi

cd ${SEQAN_BUILDS}

TOOL_CHAIN="C:/Program Files/MSBuild/12.0/Bin/MSBuild.exe"

rm -rf CMakeCache.txt CMakeFiles

APPS=$(find ${SEQAN_SRC}/apps -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)

for a in ${APPS}
do
        echo "################  Packaging app " ${a}
        echo

        APPS_PACKAGES="${SEQAN_PACKAGES}/${a}"
        mkdir -p ${APPS_PACKAGES}
        BLA="Visual Studio 14 2015 Win64"
        CMD="cmake ${SEQAN_SRC} -G \"${BLA}\" -DCPACK_OUTPUT_FILE_PREFIX=${APPS_PACKAGES} -DCMAKE_BUILD_TYPE=Release ${FLAGS} -DSEQAN_BUILD_SYSTEM=APP:${a}"
        echo ${CMD}
        eval ${CMD}
        
        if [ "$a" == "sak" ]
        then
          CMD="cmake --build . --config Release --target apps/${a}/sak_doc"
          echo "${CMD}"
          eval ${CMD}
        fi
         
        CMD="cmake --build . --config Release --target PACKAGE"
        echo "${CMD}"
        eval ${CMD}
        echo -rf *
        rm -rf *
        echo 
        echo "################  DONE"
done
