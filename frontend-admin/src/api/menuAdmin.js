// U2 admin menu API (US-A8): category & menu CRUD, reorder, availability toggle.
import client from './client'

// --- categories ---
export async function listCategories() {
  const { data } = await client.get('/api/admin/categories')
  return data
}
export async function createCategory(name) {
  const { data } = await client.post('/api/admin/categories', { name })
  return data
}
export async function updateCategory(id, name) {
  const { data } = await client.put(`/api/admin/categories/${id}`, { name })
  return data
}
export async function deleteCategory(id) {
  await client.delete(`/api/admin/categories/${id}`)
}
export async function reorderCategories(orderedIds) {
  await client.put('/api/admin/categories/reorder', { ordered_ids: orderedIds })
}

// --- menus ---
export async function listMenus() {
  const { data } = await client.get('/api/admin/menus')
  return data
}
export async function createMenu(payload) {
  const { data } = await client.post('/api/admin/menus', payload)
  return data
}
export async function updateMenu(id, payload) {
  const { data } = await client.put(`/api/admin/menus/${id}`, payload)
  return data
}
export async function deleteMenu(id) {
  await client.delete(`/api/admin/menus/${id}`)
}
export async function setMenuAvailability(id, available) {
  const { data } = await client.put(`/api/admin/menus/${id}/availability`, { available })
  return data
}
export async function reorderMenus(categoryId, orderedIds) {
  await client.put(`/api/admin/menus/reorder?category_id=${categoryId}`, {
    ordered_ids: orderedIds,
  })
}
