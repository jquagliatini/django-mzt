const path = require('node:path');

module.exports = {
  entry: {
    timers: path.join(__dirname, 'timers', 'static_files', 'js', 'src', 'timer.component.mjs'),
  },
  output: {
    path: path.join(__dirname, 'timers', 'static_files', 'js', 'dist'),
  },
};
