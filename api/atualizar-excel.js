// api/atualizar-excel.js
import { execSync } from 'child_process'

export const config = {
  schedule: "0 21 * * *", // Todo dia às 21h (horário de Brasília)
}

export default function handler() {
  try {
    execSync('python3 update_excel.py', { stdio: 'inherit' })
    return new Response('Excel atualizado com sucesso!', { status: 200 })
  } catch (error) {
    return new Response('Erro ao atualizar Excel', { status: 500 })
  }
}