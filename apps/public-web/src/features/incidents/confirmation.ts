export type Choice = 'valid' | 'invalid' | null;
export type LocationState = 'idle' | 'requesting' | 'ready' | 'denied' | 'outside' | 'inaccurate';
export type DemoLocation = Exclude<LocationState, 'idle' | 'requesting'>;

export interface ConfirmationState {
  choice: Choice;
  solved: boolean;
  description: string;
  location: LocationState;
}

export const initialConfirmation: ConfirmationState = {
  choice: null, solved: false, description: '', location: 'idle',
};

export type ConfirmationAction =
  | { type: 'choice'; value: Exclude<Choice, null> }
  | { type: 'solved'; value: boolean }
  | { type: 'description'; value: string }
  | { type: 'location'; value: LocationState };

export function confirmationReducer(state: ConfirmationState, action: ConfirmationAction): ConfirmationState {
  switch (action.type) {
    case 'choice': return { ...state, choice: action.value, solved: action.value === 'valid' ? state.solved : false };
    case 'solved': return { ...state, solved: state.choice === 'valid' && action.value };
    case 'description': return { ...state, description: action.value.slice(0, 2000) };
    case 'location': return { ...state, location: action.value };
  }
}
