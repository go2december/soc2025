module.exports = {
  content: [
    "./templates/**/*.html",
    "./pages/templates/**/*.html",
    "./node_modules/flyonui/dist/**/*.js",
  ],
  purge: [],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {},
  },
  variants: {
    extend: {},
  },
  plugins: [require("flyonui"), require("flyonui/plugin")],
};
