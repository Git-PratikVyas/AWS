<template>
  <div>
    <Login v-if="!role" @login="onLogin" />
    <Dashboard v-else :role="role" />
  </div>
</template>
<script>
import Login from './components/Login.vue'
import Dashboard from './components/Dashboard.vue'
export default {
  data() {
    return { role: '' }
  },
  components: { Login, Dashboard },
  methods: {
    onLogin(user) {
      this.role = user.role
    }
  }
}
</script> 