// U1 customer auth API (US-C1): table login for tablet setup.
import client from './client'

export function tableLogin(storeCode, tableNumber, password) {
  return client.post('/api/auth/table/login', {
    store_code: storeCode,
    table_number: tableNumber,
    password,
  })
}
