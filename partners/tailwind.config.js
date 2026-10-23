const shared = require('../tailwind.config.js');

module.exports = {
  ...shared,
  content: ['./partners/templates/**/*.html'],
  important: '.partner-pages',
  safelist: [],
};
