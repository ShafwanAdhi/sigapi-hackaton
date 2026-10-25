import { useReducer } from 'react';
import { Icon } from '../../components/ui/Icon';
import { confirmationReducer, initialConfirmation } from './confirmation';
import { GeolocationVerificationCard } from './GeolocationVerificationCard';
import { VerificationChoice } from './VerificationChoice';
import { PhotoUploadField } from './PhotoUploadField';
import { showDevelopmentDetails } from '../../app/presentation';

export function ConfirmationForm() {
  const [state, dispatch] = useReducer(confirmationReducer, initialConfirmation);
  return (
    <form className="verification-form" onSubmit={event => event.preventDefault()}>
      <GeolocationVerificationCard location={state.location} onLocationChange={value => dispatch({ type: 'location', value })} />

      <section id="konfirmasi" className="panel confirmation-card" aria-labelledby="confirmation-title">
        <VerificationChoice
          choice={state.choice}
          solved={state.solved}
          onChoiceChange={value => dispatch({ type: 'choice', value })}
          onSolvedChange={value => dispatch({ type: 'solved', value })}
        />
        <div className="form-field">
          <label htmlFor="description">Keterangan tambahan <span className="optional">(opsional)</span></label>
          <p id="description-help" className="field-hint description-help">Tuliskan apa yang Anda lihat dari tempat aman.</p>
          <textarea id="description" rows={4} maxLength={2000} placeholder="Contoh: Asap masih terlihat dari jalan utama." value={state.description} onChange={event => dispatch({ type: 'description', value: event.target.value })} aria-describedby="description-help description-count" />
          <span id="description-count" className="character-count">{state.description.length.toLocaleString('id-ID')} / 2.000 karakter</span>
        </div>

        <PhotoUploadField />

        <div className="submit-area">
          <button className={'button button-primary w-full' + (showDevelopmentDetails ? '' : ' presentation-action')} type="submit" disabled aria-describedby={showDevelopmentDetails ? 'submit-reason prototype-note' : undefined}>Kirim Konfirmasi<Icon name="arrow" size={18} /></button>
          {showDevelopmentDetails && <p id="submit-reason" className="submit-hint">{state.location === 'ready' ? 'Hasil lokasi masih simulasi. Pengiriman belum tersedia.' : 'Pengiriman konfirmasi belum tersedia.'}</p>}
          {showDevelopmentDetails && <p id="prototype-note" className="prototype-note"><Icon name="lock" size={14} />Prototipe tanpa backend. Jawaban belum dikirim atau disimpan.</p>}
        </div>
      </section>
    </form>
  );
}
