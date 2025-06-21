<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>AI-Powered SaaS Dashboard</h1>
      <div v-if="authStore.isLoggedIn" class="user-info">
        <span>Welcome, {{ authStore.userEmail }}</span>
        <button @click="authStore.logout()" class="logout-button">Logout</button>
      </div>
    </header>

    <div v-if="!authStore.isLoggedIn" class="login-container">
      <h2>Please log in</h2>
      <p>Since a full Cognito UI is not implemented, use these buttons to simulate login.</p>
      <div class="mock-login-buttons">
        <button @click="mockLoginAsAdmin">Login as Admin</button>
        <button @click="mockLoginAsUser">Login as User</button>
      </div>
    </div>

    <div v-else>
      <div class="admin-actions" v-if="authStore.isAdmin">
        <h2>Admin Panel</h2>
        <button @click="triggerSalesforceSync">Trigger Manual Salesforce Sync</button>
        <p v-if="syncMessage" class="sync-message">{{ syncMessage }}</p>
      </div>
      
      <div class="main-content">
        <AIAgent />
        <Customers />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AIAgent from './AIAgent.vue';
import Customers from './Customers.vue';

const authStore = useAuthStore();
const syncMessage = ref('');

// --- MOCK LOGIN FUNCTIONALITY ---
// In a real application, you would get this token from Cognito after a successful login.
const mockAdminToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFkbWluIFVzZXIiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiY29nbml0bzpncm91cHMiOlsiYWRtaW5zIl0sImlhdCI6MTUxNjIzOTAyMn0.tQ_xT-3eoEaYlpr2W2T5e_4-D6-Jz-b4G2eP5aW8z-k';
const mockUserToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEiLCJuYW1lIjoiUmVndWxhciBVc2VyIiwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwiY29nbml0bzpncm91cHMiOlsidXNlcnMiXSwiaWF0IjoxNTE2MjM5MDIyfQ.Jv6Vj-1q_zV-c3b-K5l-jH-n5N-yX_tY-rP3oE-d8aQ';

function mockLoginAsAdmin() {
  authStore.login(mockAdminToken);
}

function mockLoginAsUser() {
  authStore.login(mockUserToken);
}
// --- END MOCK LOGIN ---

async function triggerSalesforceSync() {
  syncMessage.value = 'Syncing...';
  try {
    const response = await fetch('/api/salesforce/sync', { // Assuming API gateway is proxied
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.idToken}`
      }
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Sync failed');
    }
    syncMessage.value = data.message || 'Sync completed successfully!';
  } catch (error) {
    syncMessage.value = `Error: ${error.message}`;
  }
}
</script>

<style scoped>
/* Add some basic styling for the dashboard */
.dashboard {
  font-family: sans-serif;
  padding: 1rem;
}
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ccc;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.login-container {
  text-align: center;
  padding: 2rem;
  border: 1px solid #eee;
  border-radius: 8px;
}
.mock-login-buttons button {
  margin: 0 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
}
.admin-actions {
  background-color: #f0f8ff;
  border: 1px solid #d1e7fd;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}
.sync-message {
  margin-top: 1rem;
  font-style: italic;
}
.main-content {
  margin-top: 1rem;
}
</style> 