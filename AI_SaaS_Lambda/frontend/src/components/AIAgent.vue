<template>
  <div>
    <h2>Ask the AI Agent</h2>
    <input v-model="prompt" placeholder="Enter your question" />
    <button @click="askAI">Ask</button>
    <div v-if="response">
      <h3>Response:</h3>
      <p>{{ response }}</p>
    </div>
  </div>
</template>
<script>
export default {
  data() {
    return { prompt: '', response: '' }
  },
  methods: {
    async askAI() {
      const res = await fetch('/api/ai/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': 'your-secure-api-key' },
        body: JSON.stringify({ prompt: this.prompt })
      });
      const data = await res.json();
      this.response = data.response;
    }
  }
}
</script> 