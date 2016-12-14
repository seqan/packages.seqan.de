#!/bin/sh

SEQAN_SRC=$1
SEQAN_BUILDS=$2
MARCH="i686"
SEQAN_PACKAGES="C:/seqan-release/package_db"

VS="Visual Studio 14 2015"
COMP="Intel C++ Compiler 16.0"

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

rm -rf CMakeCache.txt CMakeFiles

APPS=$(find ${SEQAN_SRC}/apps -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)

for a in ${APPS}
do
    echo "################  Packaging app " ${a}
    echo

    APPS_PACKAGES="${SEQAN_PACKAGES}/${a}"
    mkdir -p ${APPS_PACKAGES}
 
    CMD="cmake ${SEQAN_SRC} -G\"${VS}\" -T \"${COMP}\" -DCPACK_OUTPUT_FILE_PREFIX=${APPS_PACKAGES} -DCMAKE_BUILD_TYPE=Release ${FLAGS} -DSEQAN_BUILD_SYSTEM=APP:${a}"
    echo ${CMD}
    eval ${CMD}
    
    if [ "$a" == "sak" ]
    then
      CMD="cmake --build . --config Release --target apps/${a}/sak_doc"
      echo "${CMD}"
      ${CMD}
    fi
     
    CMD="cmake --build . --config Release --target PACKAGE"
    echo "${CMD}"
    ${CMD}
    echo -rf *
    rm -rf *
    echo 
    echo "################  DONE"
done

#echo "Packaging all apps"
#echo
#
#CMD="cmake ${SEQAN_SRC} -DCMAKE_BUILD_TYPE=Release ${FLAGS} -DSEQAN_BUILD_SYSTEM=SEQAN_RELEASE_APPS"
#echo ${CMD}
#${CMD}
#
#CMD="make package"
#echo ${CMD}
#${CMD}
#
#echo

