<template>
  <div class="todo-list">
    <h2>Todo List</h2>

    <div class="input-row">
      <input
        v-model="newTodoText"
        @keyup.enter="addTodo"
        placeholder="What needs to be done?"
      />
      <button @click="addTodo">Add</button>
    </div>

    <div class="filters">
      <button
        v-for="f in filterOptions"
        :key="f.value"
        :class="{ active: currentFilter === f.value }"
        @click="currentFilter = f.value"
      >
        {{ f.label }}
      </button>
    </div>

    <transition-group name="list" tag="div">
      <TodoItem
        v-for="todo in filteredTodos"
        :key="todo.id"
        :todo="todo"
        @toggle="toggleTodo"
        @remove="removeTodo"
      />
    </transition-group>

    <p class="summary">
      {{ remainingCount }} items left
      <span v-if="doneCount > 0">
        | <a href="#" @click.prevent="clearCompleted">Clear completed ({{ doneCount }})</a>
      </span>
    </p>
  </div>
</template>

<script>
import Vue from 'vue'
import TodoItem from './TodoItem.vue'
import EventBus from '../utils/eventBus'

export default {
  name: 'TodoList',
  components: { TodoItem },
  data() {
    return {
      todos: [],
      newTodoText: '',
      currentFilter: 'all',
      nextId: 1,
      filterOptions: [
        { label: 'All', value: 'all' },
        { label: 'Active', value: 'active' },
        { label: 'Completed', value: 'completed' }
      ]
    }
  },
  computed: {
    filteredTodos() {
      if (this.currentFilter === 'active') {
        return this.todos.filter(t => !t.done)
      }
      if (this.currentFilter === 'completed') {
        return this.todos.filter(t => t.done)
      }
      return this.todos
    },
    remainingCount() {
      return this.todos.filter(t => !t.done).length
    },
    doneCount() {
      return this.todos.filter(t => t.done).length
    }
  },
  created() {
    EventBus.$on('user-added', this.onUserAdded)
  },
  beforeDestroy() {
    EventBus.$off('user-added', this.onUserAdded)
  },
  methods: {
    addTodo() {
      const text = this.newTodoText.trim()
      if (!text) return
      Vue.set(this.todos, this.todos.length, {
        id: this.nextId++,
        text,
        done: false,
        createdAt: Date.now()
      })
      this.newTodoText = ''
    },
    toggleTodo(id) {
      const todo = this.todos.find(t => t.id === id)
      if (todo) {
        Vue.set(todo, 'done', !todo.done)
      }
    },
    removeTodo(id) {
      const idx = this.todos.findIndex(t => t.id === id)
      if (idx !== -1) {
        Vue.delete(this.todos, idx)
      }
    },
    clearCompleted() {
      this.todos = this.todos.filter(t => !t.done)
    },
    onUserAdded(payload) {
      this.addTodoFromEvent(`New user added (total: ${payload.count})`)
    },
    addTodoFromEvent(text) {
      Vue.set(this.todos, this.todos.length, {
        id: this.nextId++,
        text,
        done: false,
        createdAt: Date.now()
      })
    }
  }
}
</script>

<style scoped>
.todo-list { max-width: 500px; margin: 0 auto; }
.input-row { display: flex; gap: 8px; margin-bottom: 16px; }
.input-row input { flex: 1; padding: 8px; font-size: 16px; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
.filters button { padding: 4px 12px; border: 1px solid #ddd; background: white; cursor: pointer; border-radius: 4px; }
.filters button.active { background: #42b983; color: white; border-color: #42b983; }
.summary { color: #666; margin-top: 16px; }
.summary a { color: #e74c3c; }
.list-enter-active, .list-leave-active { transition: all 0.3s; }
.list-enter, .list-leave-to { opacity: 0; transform: translateX(-20px); }
</style>
