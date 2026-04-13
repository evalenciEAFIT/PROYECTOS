// Suppress specific React deprecation warnings from Dash components
// These warnings are due to libraries (like dash-leaflet) using older lifecycle methods for compatibility.
// They do not affect the functionality of the application.

const originalWarn = console.warn;
const originalError = console.error;

const suppressedWarnings = [
    'componentWillMount',
    'componentWillReceiveProps',
    'componentWillUpdate',
    'UNSAFE_componentWillMount',
    'UNSAFE_componentWillReceiveProps',
    'UNSAFE_componentWillUpdate'
];

console.warn = function (msg, ...args) {
    if (typeof msg === 'string' && suppressedWarnings.some(warning => msg.includes(warning))) {
        return;
    }
    originalWarn.apply(console, [msg, ...args]);
};

console.error = function (msg, ...args) {
    if (typeof msg === 'string' && suppressedWarnings.some(warning => msg.includes(warning))) {
        return;
    }
    originalError.apply(console, [msg, ...args]);
};
