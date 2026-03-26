<template>
  <div class="user-list">
    <h2>User Management</h2>

    <input v-focus v-model="searchQuery" placeholder="Search users..." />

    <ul>
      <li v-for="user in filteredUsers" :key="user.id">
        <span>{{ user.name | capitalize }}</span>
        <span class="email">{{ user.email }}</span>
        <span class="salary">{{ user.salary | currency }}</span>
        <button @click="removeUser(user.id)">Delete</button>
      </li>
    </ul>

    <div class="add-user">
      <input v-model="newUser.name" placeholder="Name" />
      <input v-model="newUser.email" placeholder="Email" />
      <input v-model.number="newUser.salary" placeholder="Salary" type="number" />
      <button @click="addUser">Add User</button>
    </div>

    <p>Total users: {{ users.length }}</p>
  </div>
</template>

<script>
import Vue from 'vue'
import EventBus from '../utils/eventBus'

export default {
  name: 'UserList',
  filters: {
    capitalize(value) {
      if (!value) return ''
      return value.charAt(0).toUpperCase() + value.slice(1)
    }
  },
  data() {
    return {
      searchQuery: '',
      users: [
        { id: 1, name: 'alice', email: 'alice@example.com', salary: 5000 },
        { id: 2, name: 'bob', email: 'bob@example.com', salary: 6000 },
        { id: 3, name: 'charlie', email: 'charlie@example.com', salary: 7000 }
      ],
      newUser: {
        name: '',
        email: '',
        salary: 0
      },
      nextId: 4
    }
  },
  computed: {
    filteredUsers() {
      const q = this.searchQuery.toLowerCase()
      return this.users.filter(u =>
        u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
      )
    }
  },
  created() {
    EventBus.$on('refresh-users', this.refreshUsers)
  },
  beforeDestroy() {
    EventBus.$off('refresh-users', this.refreshUsers)
  },
  methods: {
    addUser() {
      if (!this.newUser.name || !this.newUser.email) return
      Vue.set(this.users, this.users.length, {
        id: this.nextId++,
        name: this.newUser.name,
        email: this.newUser.email,
        salary: this.newUser.salary
      })
      this.newUser = { name: '', email: '', salary: 0 }
      EventBus.$emit('user-added', { count: this.users.length })
    },
    removeUser(id) {
      const idx = this.users.findIndex(u => u.id === id)
      if (idx !== -1) {
        Vue.delete(this.users, idx)
      }
    },
    refreshUsers() {
      console.log('Refreshing users...')
      this.$forceUpdate()
    }
  }
}
</script>

<style scoped>
.user-list { max-width: 600px; margin: 0 auto; }
ul { list-style: none; padding: 0; }
li { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
.email { color: #666; }
.salary { color: #42b983; font-weight: bold; }
.add-user { margin-top: 20px; display: flex; gap: 8px; }
.add-user input { padding: 6px; }
</style>
