export const authStore = {
    getToken: () => localStorage.getItem('token'),
    getRole: () => localStorage.getItem('role'),
    getUser: () => localStorage.getItem('username'),

    login: (token, role, username) => {
        localStorage.setItem('token', token);
        localStorage.setItem('role', role);
        localStorage.setItem('username', username);
    },

    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('username');
        window.location.href = '/login';
    },

    isAuthenticated: () => !!localStorage.getItem('token'),
};
