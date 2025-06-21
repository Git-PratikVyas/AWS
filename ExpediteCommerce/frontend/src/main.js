import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './main.css'
// import boto3

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')

const cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='AIAgent',
    MetricData=[{
        'MetricName': 'SuccessfulQueries',
        'Value': 1,
        'Unit': 'Count'
    }]
) 