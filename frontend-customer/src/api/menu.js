// U2 customer menu API. Grouped-by-category menu for the table screen (US-C2).
import client from './client'

export async function fetchMenu() {
  const { data } = await client.get('/api/menu')
  return data // [{ id, name, display_order, menus: [{ id, name, price, description, image_url, available }] }]
}
