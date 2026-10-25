import { Icon } from '../../components/ui/Icon';
import type { Choice } from './confirmation';

export function VerificationChoice({ choice, solved, onChoiceChange, onSolvedChange }: {
  choice: Choice;
  solved: boolean;
  onChoiceChange: (value: Exclude<Choice, null>) => void;
  onSolvedChange: (value: boolean) => void;
}) {
  return (
    <fieldset className="choice-fieldset" aria-describedby="choice-help">
      <legend id="confirmation-title">Apakah kejadian benar terjadi?</legend>
      <p id="choice-help" className="field-hint choice-help">Pilih satu jawaban berdasarkan kondisi yang Anda ketahui.</p>
      <label className={'choice-card choice-valid' + (choice === 'valid' ? ' selected' : '')}>
        <Icon name="checkCircle" size={24} className="choice-icon" />
        <span>Ya, kejadian benar terjadi</span>
        <input type="radio" name="choice" value="valid" checked={choice === 'valid'} onChange={() => onChoiceChange('valid')} required />
      </label>
      <label className={'choice-card choice-invalid' + (choice === 'invalid' ? ' selected' : '')}>
        <Icon name="crossCircle" size={24} className="choice-icon" />
        <span>Tidak, informasi kejadian tidak sesuai</span>
        <input type="radio" name="choice" value="invalid" checked={choice === 'invalid'} onChange={() => onChoiceChange('invalid')} />
      </label>

      {choice === 'valid' && <div className="solved-block">
        <label className="checkbox-label">
          <input type="checkbox" checked={solved} onChange={event => onSolvedChange(event.target.checked)} aria-describedby="solved-help solved-source" />
          <span>Kebakaran sudah tertangani<span className="optional"> (opsional)</span></span>
        </label>
        <p id="solved-help" className="field-hint">Centang jika berdasarkan pengamatan Anda kejadian telah selesai atau api sudah tertangani.</p>
        <p id="solved-source" className="field-hint">Klaim pengguna, bukan penutupan resmi oleh pihak berwenang.</p>
      </div>}
    </fieldset>
  );
}
