// U1 admin auth API calls (US-A1, US-A4).
import client from './client'

export function adminLogin(storeCode, username, password) {
  return client.post('/api/auth/admin/login', {
    store_code: storeCode,
    username,
    password,
  })
}

export function listTables() {
  return client.get('/api/admin/tables')
}

export function createTable(tableNumber, password) {
  return client.post('/api/admin/tables', {
    table_number: tableNumber,
    password,
  })
}

export function updateTable(id, { tableNumber, password }) {
  const body = {}
  if (tableNumber !== undefined && tableNumber !== null) body.table_number = tableNumber
  if (password) body.password = password
  return client.put(`/api/admin/tables/${id}`, body)
}
