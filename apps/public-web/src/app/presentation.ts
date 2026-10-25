// Public presentation stays clean. Local simulation controls are opt-in for developers.
export const showDevelopmentDetails = new URLSearchParams(window.location.search).get('dev') === '1';
