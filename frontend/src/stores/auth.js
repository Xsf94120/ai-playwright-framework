import { defineStore } from 'pinia'
import api, { getToken, setToken } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: getToken(),
    username: localStorage.getItem('ai_pw_username') || '',
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(username, password) {
      const { data } = await api.post('/auth/login', { username, password })
      this.token = data.access_token
      this.username = data.username
      setToken(data.access_token)
      localStorage.setItem('ai_pw_username', data.username)
    },
    logout() {
      this.token = ''
      this.username = ''
      setToken('')
      localStorage.removeItem('ai_pw_username')
    },
  },
})
