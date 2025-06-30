<template>
  <div>
    <h2>Login</h2>
    <input v-model="username" placeholder="Username" />
    <input v-model="password" type="password" placeholder="Password" />
    <button @click="login">Login</button>
    <div v-if="error">{{ error }}</div>
  </div>
</template>
<script>
export default {
  data() {
    return { username: '', password: '', error: '' }
  },
  methods: {
    login() {
      if (this.username === 'admin' && this.password === 'admin') {
        this.$emit('login', { role: 'admin' })
      } else {
        this.error = 'Invalid credentials';
      }
    }
  }
}
</script> 