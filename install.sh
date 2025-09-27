#!/usr/bin/env bash

set -euo pipefail

BIN_DIR=/usr/local/bin/
BIN_NAME=prog

BIN_PATH=$BIN_DIR$BIN_NAME

check_installed() {
  (&>/dev/null python -c "import $1") || { echo "Error: python module $1 is not installed."; exit 1; }
}

confirm() {
  read -p "$1? [Y/n] " usrin
  [[ $usrin = *[![:space:]]* ]] || return 0 # Check whether input contains just whitespace.
  case $usrin in # Check whether user entered "yes".
    y|Y)
      return 0
      ;;
    *)
      return 1
  esac
}

check_installed click
check_installed serial

echo "Installing to $BIN_PATH ..."

if [ -f $BIN_PATH ]; then
  confirm "Warning: symlink $BIN_PATH exists already. Continue anyways" || exit 1
  sudo rm $BIN_PATH
fi

chmod +x ./cli/cli.py
sudo ln -s $(realpath ./cli/cli.py) $BIN_PATH 

confirm "Do you want to flash the programmer now" && ./flash.sh

echo "Installation completed successfully."
