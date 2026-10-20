export function arrayBufferToBase64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

export function base64ToArrayBuffer(b64: string): ArrayBuffer {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes.buffer as ArrayBuffer
}

const PBKDF2_ITERATIONS = 600000
const SALT_LENGTH = 16
const IV_LENGTH = 12

export type EncryptedPayload = {
  encrypted: string
  iv: string
  salt: string
}

/**
 * Derive an AES-256-GCM key from a passphrase + salt using PBKDF2.
 */
async function deriveKey(passphrase: string, salt: ArrayBuffer): Promise<CryptoKey> {
  const encoder = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(passphrase).buffer as ArrayBuffer,
    'PBKDF2',
    false,
    ['deriveKey'],
  )

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: PBKDF2_ITERATIONS,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  )
}

/**
 * Encrypt a plaintext string using the passphrase.
 * Returns the encrypted data, IV, and salt as base64 strings.
 */
export async function encryptField(plaintext: string, passphrase: string): Promise<EncryptedPayload> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LENGTH)).buffer as ArrayBuffer
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH)).buffer as ArrayBuffer
  const key = await deriveKey(passphrase, salt)

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    new TextEncoder().encode(plaintext).buffer as ArrayBuffer,
  )

  return {
    encrypted: arrayBufferToBase64(encrypted),
    iv: arrayBufferToBase64(iv),
    salt: arrayBufferToBase64(salt),
  }
}

/**
 * Decrypt a ciphertext that was encrypted with encryptField.
 */
export async function decryptField(
  payload: EncryptedPayload,
  passphrase: string,
): Promise<string> {
  const encrypted = base64ToArrayBuffer(payload.encrypted)
  const iv = base64ToArrayBuffer(payload.iv)
  const salt = base64ToArrayBuffer(payload.salt)
  const key = await deriveKey(passphrase, salt)

  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    key,
    encrypted,
  )

  return new TextDecoder().decode(decrypted)
}

/**
 * Derive an AES-256-GCM key from raw Input Keying Material (IKM) using HKDF-SHA256.
 *
 * This is used with WebAuthn PRF output (32-byte IKM) to derive a domain-separated
 * encryption key bound to a specific purpose (e.g., "passphrase-encryption").
 */
export async function deriveKeyFromIKM(
  ikm: ArrayBuffer,
  info: string,
): Promise<CryptoKey> {
  const hkdfKey = await crypto.subtle.importKey(
    'raw',
    ikm,
    'HKDF',
    false,
    ['deriveKey'],
  )

  return crypto.subtle.deriveKey(
    {
      name: 'HKDF',
      hash: 'SHA-256',
      salt: new TextEncoder().encode('MultiAgentResearchSystem-v1'),
      info: new TextEncoder().encode(info),
    },
    hkdfKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  )
}

/**
 * Encrypt a plaintext string using a raw 32-byte key (e.g., from WebAuthn PRF).
 * The key is first derived through HKDF for domain separation, then used for AES-256-GCM.
 */
export async function encryptWithRawKey(
  plaintext: string,
  keyBytes: ArrayBuffer,
  purpose: string = 'passphrase-encryption',
): Promise<EncryptedPayload> {
  const key = await deriveKeyFromIKM(keyBytes, purpose)
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH)).buffer as ArrayBuffer

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    new TextEncoder().encode(plaintext).buffer as ArrayBuffer,
  )

  return {
    encrypted: arrayBufferToBase64(encrypted),
    iv: arrayBufferToBase64(iv),
    salt: '',
  }
}

/**
 * Decrypt a ciphertext that was encrypted with encryptWithRawKey.
 */
export async function decryptWithRawKey(
  payload: EncryptedPayload,
  keyBytes: ArrayBuffer,
  purpose: string = 'passphrase-encryption',
): Promise<string> {
  const key = await deriveKeyFromIKM(keyBytes, purpose)
  const iv = base64ToArrayBuffer(payload.iv)
  const encrypted = base64ToArrayBuffer(payload.encrypted)

  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    key,
    encrypted,
  )

  return new TextDecoder().decode(decrypted)
}
