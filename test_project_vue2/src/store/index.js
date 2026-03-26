import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    user: null,
    theme: 'light',
    notifications: []
  },
  getters: {
    isLoggedIn(state) {
      return !!state.user
    },
    unreadCount(state) {
      return state.notifications.filter(n => !n.read).length
    }
  },
  mutations: {
    SET_USER(state, user) {
      Vue.set(state, 'user', user)
    },
    SET_THEME(state, theme) {
      state.theme = theme
    },
    ADD_NOTIFICATION(state, notification) {
      Vue.set(state.notifications, state.notifications.length, {
        ...notification,
        id: Date.now(),
        read: false
      })
    },
    MARK_READ(state, id) {
      const n = state.notifications.find(n => n.id === id)
      if (n) {
        Vue.set(n, 'read', true)
      }
    },
    CLEAR_NOTIFICATIONS(state) {
      Vue.set(state, 'notifications', [])
    }
  },
  actions: {
    login({ commit }, credentials) {
      return new Promise((resolve) => {
        setTimeout(() => {
          commit('SET_USER', { name: credentials.username, role: 'admin' })
          commit('ADD_NOTIFICATION', { message: 'Login successful' })
          resolve()
        }, 500)
      })
    },
    logout({ commit }) {
      commit('SET_USER', null)
      commit('CLEAR_NOTIFICATIONS')
    }
  }
})
