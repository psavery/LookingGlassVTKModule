#!/usr/bin/env bash
set -ev

deps_dir=$PWD/_deps

#### Install cibuildwheel ####
pip install cibuildwheel

if [[ $RUNNER_OS == "Windows" ]]; then
    # Install wget
    choco install wget -y
    holoplaycore_lib=Win64/HoloPlayCore.lib
elif [[ $RUNNER_OS == "macOS" ]]; then
    # Install ninja
    brew install ninja
    holoplaycore_lib=macos/libHoloPlayCore.dylib

    # VTK is expecting the xcode path to be slightly different
    ln -s /Applications/Xcode_13.1.app/ /Applications/Xcode-13.1.app
elif [[ $RUNNER_OS == "Linux" ]]; then
    holoplaycore_lib=linux/libHoloPlayCore.so
fi

#### Install HoloPlayCore ####
holoplaycore_url=https://www.paraview.org/files/dependencies/HoloPlayCore-0.1.1-Open-20200923.tar.gz
output_directory=$deps_dir/HoloPlayCore

mkdir -p $output_directory
wget -qO- $holoplaycore_url | tar xz -C $output_directory --strip-components=1

include_dir=$output_directory/HoloPlayCore/include
lib_path=$output_directory/HoloPlayCore/dylib

echo "HOLOPLAYCORE_INCLUDE_DIR=$include_dir" >> $GITHUB_ENV
echo "HOLOPLAYCORE_LIBRARY=$lib_path/$holoplaycore_lib" >> $GITHUB_ENV

#### Install VTKExternalModule ####
clone_path=$deps_dir/VTKExternalModule
git clone https://github.com/KitwareMedical/VTKExternalModule $clone_path
echo "VTK_EXTERNAL_MODULE_PATH=$clone_path" >> $GITHUB_ENV

#### Tell cibuildwheel where it will find the wheel sdk ####
echo "VTK_WHEEL_SDK_PATH=$deps_dir/vtk-wheel-sdk" >> $GITHUB_ENV

if [[ $RUNNER_OS == "Linux" ]]; then
    # In docker on Linux, everything will be under /project instead of $PWD
    echo "HOLOPLAYCORE_INCLUDE_DIR=/project/$(echo $HOLOPLAYCORE_INCLUDE_DIR | sed 's/.*\(_deps\)/\1/g')" >> $GITHUB_ENV
    echo "HOLOPLAYCORE_LIBRARY=/project/$(echo $HOLOPLAYCORE_LIBRARY | sed 's/.*\(_deps\)/\1/g')" >> $GITHUB_ENV
    echo "VTK_EXTERNAL_MODULE_PATH=/project/$(echo $VTK_EXTERNAL_MODULE_PATH | sed 's/.*\(_deps\)/\1/g')" >> $GITHUB_ENV
    echo "VTK_WHEEL_SDK_PATH=/project/$(echo $VTK_WHEEL_SDK_PATH | sed 's/.*\(_deps\)/\1/g')" >> $GITHUB_ENV
fi
