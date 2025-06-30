<template>
  <div>
    <h2>Customer List</h2>
    <ul>
      <li v-for="c in customers" :key="c.Id">{{ c.Name }} ({{ c.Email }})</li>
    </ul>
  </div>
</template>
<script>
export default {
  data() {
    return { customers: [] }
  },
  async mounted() {
    const res = await fetch('/api/customers', {
      headers: { 'x-api-key': 'your-secure-api-key' }
    });
    this.customers = await res.json();
  }
}
</script> 