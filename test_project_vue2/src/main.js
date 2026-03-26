import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

Vue.config.productionTip = false

// 全局过滤器
Vue.filter('capitalize', function (value) {
  if (!value) return ''
  value = value.toString()
  return value.charAt(0).toUpperCase() + value.slice(1)
})

Vue.filter('currency', function (value) {
  if (typeof value !== 'number') return value
  return '$' + value.toFixed(2)
})

// 全局混入
Vue.mixin({
  created() {
    if (this.$options.debugLog) {
      console.log(`[Debug] ${this.$options.name} created`)
    }
  }
})

// 全局自定义指令
Vue.directive('focus', {
  inserted(el) {
    el.focus()
  }
})

// 挂载全局属性
Vue.prototype.$appName = 'Vue2 Demo App'
Vue.prototype.$api = {
  baseUrl: 'https://api.example.com'
}

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
