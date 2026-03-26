<template>
  <div class="todo-item" :class="{ completed: todo.done }">
    <input type="checkbox" :checked="todo.done" @change="toggle" />
    <span class="text">{{ todo.text }}</span>
    <span class="date">{{ todo.createdAt | formatDate }}</span>
    <button @click="$emit('remove', todo.id)">×</button>
  </div>
</template>

<script>
export default {
  name: 'TodoItem',
  props: {
    todo: {
      type: Object,
      required: true
    }
  },
  filters: {
    formatDate(value) {
      if (!value) return ''
      const d = new Date(value)
      return d.toLocaleDateString()
    }
  },
  methods: {
    toggle() {
      this.$emit('toggle', this.todo.id)
    }
  }
}
</script>

<style scoped>
.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-bottom: 1px solid #eee;
}
.todo-item.completed .text {
  text-decoration: line-through;
  color: #999;
}
.date { color: #999; font-size: 0.85em; }
button { background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; padding: 2px 8px; }
</style>
