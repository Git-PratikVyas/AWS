import { defineStore } from 'pinia'
import jwt_decode from 'jwt-decode'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    idToken: localStorage.getItem('idToken') || null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.idToken,
    isAdmin: (state) => {
      if (!state.idToken) return false;
      
      try {
        const decodedToken = jwt_decode(state.idToken);
        const groups = decodedToken['cognito:groups'] || [];
        return groups.includes('admins');
      } catch (error) {
        console.error("Invalid token:", error);
        return false;
      }
    },
    userEmail: (state) => {
      if (!state.idToken) return null;
      try {
        const decodedToken = jwt_decode(state.idToken);
        return decodedToken.email;
      } catch (error) {
        return null;
      }
    }
  },
  actions: {
    login(token) {
      this.idToken = token;
      localStorage.setItem('idToken', token);
    },
    logout() {
      this.idToken = null;
      localStorage.removeItem('idToken');
      // In a real app, you would redirect to a login page
      window.location.reload();
    }
  }
}) 