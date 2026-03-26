import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../components/TodoList.vue')
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../components/UserList.vue')
  },
  {
    path: '/todos',
    name: 'Todos',
    component: () => import('../components/TodoList.vue')
  },
  {
    path: '*',
    redirect: '/'
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

router.beforeEach((to, from, next) => {
  console.log(`Navigating from ${from.path} to ${to.path}`)
  next()
})

export default router
