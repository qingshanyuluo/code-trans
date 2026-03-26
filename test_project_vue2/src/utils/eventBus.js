/**
 * Vue 2 Event Bus — 用于非父子组件通信
 * Vue 3 中已移除 $on/$off/$once，需迁移到 mitt 或 tiny-emitter
 */
import Vue from 'vue'

const EventBus = new Vue()

export default EventBus
