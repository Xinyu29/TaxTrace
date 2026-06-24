import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export const getDashboard   = () => api.get('/api/dashboard').then(r => r.data)
export const getInvoices    = () => api.get('/api/invoices').then(r => r.data)
export const getInvoice     = id => api.get(`/api/invoices/${id}`).then(r => r.data)
export const invoiceAction  = (id, action) => api.post(`/api/invoices/${id}/action`, { action }).then(r => r.data)
export const getDiscrepancy = id => api.get(`/api/discrepancies/${id}`).then(r => r.data)
export const getDiscrepancies = () => api.get('/api/discrepancies').then(r => r.data)
export const getAuditLog    = () => api.get('/api/audit-log').then(r => r.data)
export const getComms       = () => api.get('/api/comms').then(r => r.data)
export const getAnalytics   = () => api.get('/api/analytics').then(r => r.data)
export const analyzeInvoice = payload => api.post('/api/analyze', payload).then(r => r.data)
export const draftEmail     = payload => api.post('/api/draft-email', payload).then(r => r.data)