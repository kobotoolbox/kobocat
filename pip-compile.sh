#!/bin/bash
for in_file in dependencies/pip/*.in
do
    # pass any arguments to pip-compile
    # useful for switches like `--upgrade-package`
    pip-compile "$@" "$in_file"
done
