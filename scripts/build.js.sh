#!/bin/bash

npx spack
npx swc \
  --config-file .swcrc \
  -o ./timers/static_files/js/dist/timers.min.js \
  ./timers/static_files/js/dist/timers.js
rm ./timers/static_files/js/dist/timers.js
rm ./timers/static_files/js/dist/timers.js.map