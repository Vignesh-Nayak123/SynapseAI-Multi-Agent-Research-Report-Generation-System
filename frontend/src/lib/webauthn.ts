/**
 * WebAuthn PRF Extension — biometric unlock for the zero-knowledge passphrase.
 *
 * Uses the WebAuthn PRF (Pseudo-Random Function) extension to derive
 * deterministic 32-byte key material from a platform authenticator
 * (fingerprint, Face ID, Windows Hello, etc.).
 *
 * The PRF output is deterministic for a given (credential, salt) pair,
 * allowing us to encrypt the user's passphrase with the biometric key
 * and decrypt it later without the user having to retype it.
 */

import { arrayBufferToBase64, base64ToArrayBuffer } from './crypto'

const PRF_SALT = new TextEncoder().encode('multi-agent-research-system-passphrase-unlock-v1')

const RP_NAME = 'Multi-Agent Research System'

/**
 * Check whether the browser + platform authenticator supports the PRF extension.
 */
export async function isWebAuthnPRFAvailable(): Promise<boolean> {
  if (!window.PublicKeyCredential || typeof PublicKeyCredential.getClientCapabilities !== 'function') {
    return false
  }
  try {
    const capabilities = await PublicKeyCredential.getClientCapabilities()
    return capabilities.prf === true
  } catch {
    return false
  }
}

/**
 * Check whether a biometric credential has been registered (stored in localStorage).
 */
export function hasBiometricCredential(): boolean {
  try {
    return !!localStorage.getItem('webauthn-credential-id')
  } catch {
    return false
  }
}

/**
 * Register a new platform credential with the PRF extension enabled and
 * evaluate the PRF to get deterministic key material in a single ceremony.
 *
 * @returns The base64-encoded credential ID and the 32-byte PRF output (key material).
 */
export async function registerBiometricKey(): Promise<{
  credentialId: string
  keyMaterial: ArrayBuffer
}> {
  if (!window.PublicKeyCredential) {
    throw new Error('WebAuthn is not supported in this browser')
  }

  const challenge = crypto.getRandomValues(new Uint8Array(32))
  const userId = crypto.getRandomValues(new Uint8Array(16))

  const credential = (await navigator.credentials.create({
    publicKey: {
      challenge,
      rp: { name: RP_NAME },
      user: {
        id: userId,
        name: 'user',
        displayName: 'User',
      },
      pubKeyCredParams: [
        { alg: -7, type: 'public-key' as const },
        { alg: -257, type: 'public-key' as const },
      ],
      authenticatorSelection: {
        authenticatorAttachment: 'platform',
        userVerification: 'required',
      },
      extensions: {
        prf: {
          eval: { first: PRF_SALT },
        },
      },
    },
  })) as PublicKeyCredential | null

  if (!credential) {
    throw new Error('Biometric registration was cancelled')
  }

  const prfResult = credential.getClientExtensionResults()?.prf
  if (!prfResult?.results?.first) {
    throw new Error(
      'This authenticator does not support the PRF extension. ' +
        'Try using a different device or authenticator (e.g., fingerprint sensor, Face ID, Windows Hello).',
    )
  }

  const credentialId = arrayBufferToBase64(credential.rawId)

  return {
    credentialId,
    keyMaterial: prfResult.results.first as ArrayBuffer,
  }
}

/**
 * Authenticate with a previously registered biometric credential and
 * derive the same PRF key material.
 *
 * @param credentialIdBase64 The base64-encoded credential ID from registration.
 * @returns The 32-byte PRF output (same as registration).
 */
export async function unlockWithBiometric(credentialIdBase64: string): Promise<ArrayBuffer> {
  const credentialId = base64ToArrayBuffer(credentialIdBase64)

  const assertion = (await navigator.credentials.get({
    publicKey: {
      challenge: crypto.getRandomValues(new Uint8Array(32)),
      allowCredentials: [
        {
          id: credentialId,
          type: 'public-key',
        },
      ],
      userVerification: 'required',
      extensions: {
        prf: {
          eval: { first: PRF_SALT },
        },
      },
    },
  })) as PublicKeyCredential | null

  if (!assertion) {
    throw new Error('Biometric unlock was cancelled')
  }

  const prfResult = assertion.getClientExtensionResults()?.prf
  if (!prfResult?.results?.first) {
    throw new Error('Biometric unlock failed — could not derive key from authenticator')
  }

  return prfResult.results.first as ArrayBuffer
}

// ─── Recovery word list (128 short, unambiguous English words) ───────

const RECOVERY_WORDS = [
  'apple', 'beach', 'cabin', 'dance', 'eagle', 'fable', 'gauge', 'honey',
  'ivory', 'jewel', 'kayak', 'lemon', 'mango', 'noble', 'ocean', 'piano',
  'quilt', 'raven', 'sable', 'tiger', 'umbra', 'vivid', 'whale', 'xenon',
  'yacht', 'zebra', 'amber', 'bloom', 'coral', 'dawn', 'ember', 'frost',
  'glade', 'haven', 'iris', 'jade', 'keeps', 'latch', 'mirth', 'night',
  'olive', 'pearl', 'quest', 'ridge', 'snowy', 'trail', 'ultra', 'vault',
  'wheat', 'alder', 'birch', 'crane', 'deer', 'elm', 'fern', 'grape',
  'heath', 'islet', 'koi', 'larch', 'maple', 'nutmeg', 'orchid', 'pine',
  'robin', 'spruce', 'thorn', 'vine', 'wren', 'aster', 'brook', 'cliff',
  'dove', 'fir', 'gull', 'hill', 'ibis', 'jay', 'kiwi', 'lark', 'moss',
  'newt', 'owl', 'puffin', 'quail', 'reef', 'swan', 'tern', 'ursa',
  'vole', 'wasp', 'yak', 'anvil', 'barge', 'cello', 'drum', 'easel',
  'flute', 'gong', 'harp', 'kazoo', 'lute', 'organ', 'pixel', 'quill',
  'relic', 'scone', 'tint', 'viola', 'whim', 'yarn', 'zinc', 'ardor',
  'bling', 'chime', 'dream', 'echo', 'flash', 'gleam', 'humor', 'image',
  'joke', 'knack', 'light', 'magic', 'onyx', 'prism', 'rider', 'shine',
  'trick', 'unity', 'vigor', 'waltz', 'youth', 'zeal',
]

/**
 * Generate a human-readable 5-word recovery code.
 * ~128^5 ≈ 3.4×10¹⁰ combinations, backed by PBKDF2 with 600K iterations.
 */
export function generateRecoveryCode(): string {
  const words: string[] = []
  const rand = crypto.getRandomValues(new Uint32Array(5))
  for (let i = 0; i < 5; i++) {
    const idx = rand[i] % RECOVERY_WORDS.length
    words.push(RECOVERY_WORDS[idx])
  }
  return words.join('-')
}

/**
 * Check whether recovery data exists in localStorage.
 */
export function hasRecoveryData(): boolean {
  try {
    return !!localStorage.getItem('webauthn-recovery-encrypted')
  } catch {
    return false
  }
}

/**
 * Load the stored recovery hint from localStorage (if any).
 */
export function getRecoveryHint(): string {
  try {
    return localStorage.getItem('webauthn-recovery-hint') || ''
  } catch {
    return ''
  }
}

/**
 * Remove all stored biometric + recovery data from localStorage.
 */
export function clearBiometricCredential(): void {
  try {
    localStorage.removeItem('webauthn-credential-id')
    localStorage.removeItem('webauthn-encrypted-passphrase')
    localStorage.removeItem('webauthn-encryption-iv')
    localStorage.removeItem('webauthn-encryption-salt')
    localStorage.removeItem('webauthn-recovery-encrypted')
    localStorage.removeItem('webauthn-recovery-iv')
    localStorage.removeItem('webauthn-recovery-salt')
    localStorage.removeItem('webauthn-recovery-code-encrypted')
    localStorage.removeItem('webauthn-recovery-code-iv')
    localStorage.removeItem('webauthn-recovery-code-salt')
    localStorage.removeItem('webauthn-recovery-hint')
  } catch {
    // localStorage may not be available
  }
}
