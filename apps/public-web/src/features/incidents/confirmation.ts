export type Choice = 'valid' | 'invalid' | null;
export type LocationState = 'idle' | 'ready' | 'denied' | 'outside';
export type DemoLocation = Exclude<LocationState, 'idle'>;

export interface ConfirmationState {
  choice: Choice;
  solved: boolean;
  description: string;
  location: LocationState;
  previewed: boolean;
}

export const initialConfirmation: ConfirmationState = {
  choice: null, solved: false, description: '', location: 'idle', previewed: false,
};

export type ConfirmationAction =
  | { type: 'choice'; value: Exclude<Choice, null> }
  | { type: 'solved'; value: boolean }
  | { type: 'description'; value: string }
  | { type: 'location'; value: LocationState }
  | { type: 'preview' }
  | { type: 'edited' };

export function canPreview(state: ConfirmationState) {
  return state.choice !== null && state.location === 'ready';
}

export function confirmationReducer(state: ConfirmationState, action: ConfirmationAction): ConfirmationState {
  switch (action.type) {
    case 'choice': return { ...state, choice: action.value, solved: action.value === 'valid' ? state.solved : false, previewed: false };
    case 'solved': return { ...state, solved: state.choice === 'valid' && action.value, previewed: false };
    case 'description': return { ...state, description: action.value.slice(0, 2000), previewed: false };
    case 'location': return { ...state, location: action.value, previewed: false };
    case 'preview': return { ...state, previewed: canPreview(state) };
    case 'edited': return { ...state, previewed: false };
  }
}

export const locationCopy: Record<LocationState, { title: string; description: string }> = {
  idle: { title: 'Lokasi belum diperiksa', description: 'Konfirmasi memerlukan lokasi dalam radius 2 km dari titik kejadian.' },
  ready: { title: 'Dalam radius konfirmasi', description: 'Jarak simulasi 850 m · akurasi simulasi 25 m. Tidak menggunakan GPS perangkat.' },
  denied: { title: 'Izin lokasi belum diberikan', description: 'Pada layanan aktif, izinkan lokasi perangkat lalu coba lagi. Keadaan ini adalah simulasi.' },
  outside: { title: 'Di luar radius 2 km', description: 'Jarak simulasi 2,8 km. Konfirmasi tidak dapat dikirim dari luar radius. Jangan mendekati api demi mengisi form.' },
};
