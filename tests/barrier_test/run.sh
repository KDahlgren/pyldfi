#!/usr/bin/env bash

# run the test
(python ../../src/drivers/driver1.py -n a,b,c,d -f ./barrier_test.ded) > tmp.txt

# check if test passed (TODO: make more sophisticated)
if grep -Fxq "PROGRAM EXITED SUCCESSFULLY" tmp.txt
then
  echo "TEST PASSED"
else
  echo "TEST FAILED"
  echo "Offending output : "
  cat tmp.txt
fi

# remove the temp file to clean up directory
rm tmp.txt
