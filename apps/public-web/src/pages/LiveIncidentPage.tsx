import { useEffect,useRef,useState } from 'react';
import { SigapiHeader,PageFooter,SafetyNotice } from '../components/ui/PageShell';
import { Icon } from '../components/ui/Icon';
import { PhotoUploadField } from '../features/incidents/PhotoUploadField';
import { VerificationChoice } from '../features/incidents/VerificationChoice';
import { LiveMap } from '../features/incidents/LiveMap';
import type { Choice } from '../features/incidents/confirmation';

interface Incident {
  reference:string;title:string;summary:string;location_name:string;observed_at:string|null;
  location:{latitude:number;longitude:number};location_version:number;photo_url:string|null;
  verification:{summary:string;solved_claim_status:string};
}

const errors:Record<string,string>={OUT_OF_RADIUS:'Lokasi berada di luar radius 2 km. Konfirmasi belum disimpan.',
  STALE_LOCATION:'Lokasi sudah kedaluwarsa. Perbarui lokasi dari tempat aman.',
  INACCURATE_LOCATION:'Akurasi lokasi belum memadai. Perbarui lokasi.',
  INVALID_LOCATION_OR_INPUT:'Periksa lokasi dan isian konfirmasi.',RATE_LIMITED:'Terlalu banyak upaya. Coba lagi setelah 10 menit.',
  INCIDENT_LOCATION_CHANGED:'Titik kejadian berubah. Muat ulang halaman dan perbarui lokasi.',
  PHOTO_TOO_LARGE:'Foto melebihi 10 MB.',INVALID_PHOTO:'Foto tidak dapat dibuka.',NOT_FOUND:'Laporan tidak tersedia.'};

export function LiveIncidentPage(){
  const slug=window.location.pathname.split('/')[2]??'';
  const [incident,setIncident]=useState<Incident|null>(null);const [loading,setLoading]=useState(true);
  const [loadError,setLoadError]=useState('');const [choice,setChoice]=useState<Choice>(null);
  const [solved,setSolved]=useState(false);const [description,setDescription]=useState('');const [photo,setPhoto]=useState<File|null>(null);
  const [gps,setGps]=useState<GeolocationPosition|null>(null);const [locating,setLocating]=useState(false);const [gpsError,setGpsError]=useState('');
  const [pending,setPending]=useState(false);const [uncertain,setUncertain]=useState(false);const [error,setError]=useState('');const [receipt,setReceipt]=useState('');
  const submission=useRef<FormData|null>(null);const locationRequest=useRef(0);
  useEffect(()=>{
    if(!/^[a-f0-9]{32}$/.test(slug)){setLoadError('Laporan tidak tersedia.');setLoading(false);return;}
    const abort=new AbortController();
    fetch('/api/laporan/'+encodeURIComponent(slug),{signal:abort.signal}).then(async response=>{
      if(!response.ok)throw Error(response.status===404?'Laporan tidak tersedia.':'Laporan belum dapat dimuat. Coba muat ulang.');
      setIncident(await response.json() as Incident);
    }).catch(err=>{if(!abort.signal.aborted)setLoadError(String(err.message));}).finally(()=>{if(!abort.signal.aborted)setLoading(false);});
    return()=>{abort.abort();locationRequest.current++;};
  },[slug]);
  useEffect(()=>{if(!gps)return;const timer=window.setTimeout(()=>{setGps(null);setGpsError('Lokasi kedaluwarsa. Perbarui dari tempat aman.');},Math.max(0,60000-(Date.now()-gps.timestamp)));return()=>window.clearTimeout(timer);},[gps]);
  const locked=pending||uncertain||Boolean(receipt);
  function locate(){
    const request=++locationRequest.current;setLocating(true);setGps(null);setGpsError('');submission.current=null;
    if(!navigator.geolocation){setGpsError('Browser tidak mendukung lokasi perangkat.');setLocating(false);return;}
    navigator.geolocation.getCurrentPosition(position=>{
      if(request!==locationRequest.current)return;setLocating(false);
      if(position.coords.accuracy<=0||position.coords.accuracy>100){setGpsError('Akurasi lokasi belum memadai (maksimal 100 m). Coba lagi.');return;}
      setGps(position);
    },failure=>{if(request!==locationRequest.current)return;setLocating(false);setGpsError(failure.code===1?'Izin lokasi ditolak. Izinkan lokasi pada browser.':'Lokasi belum tersedia. Coba lagi dari tempat aman.');},
    {enableHighAccuracy:true,maximumAge:0,timeout:15000});
  }
  async function submit(event:React.FormEvent){
    event.preventDefault();if(!incident||!choice||(!gps&&!submission.current)||pending||receipt)return;
    if(!submission.current){
      if(!gps||Date.now()-gps.timestamp>60000){setError(errors.STALE_LOCATION);return;}
      const form=new FormData();form.set('request_id',crypto.randomUUID());form.set('choice',choice);
      form.set('latitude',String(gps.coords.latitude));form.set('longitude',String(gps.coords.longitude));
      form.set('accuracy_m',String(gps.coords.accuracy));form.set('gps_fix_at',new Date(gps.timestamp).toISOString());
      form.set('location_version',String(incident.location_version));form.set('description',description);
      form.set('solved',String(choice==='valid'&&solved));if(photo)form.set('photo',photo);submission.current=form;
    }
    setPending(true);setError('');
    try{
      const response=await fetch('/api/laporan/'+encodeURIComponent(slug)+'/verifications',{method:'POST',body:submission.current,signal:AbortSignal.timeout(30000)});
      const result=await response.json();
      if(!response.ok){
        if(response.status<500){submission.current=null;setUncertain(false);}else setUncertain(true);
        throw Error(errors[result.detail]??'Pengiriman belum dapat dipastikan. Coba ulang untuk memeriksa receipt yang sama.');
      }
      if(typeof result.receipt_id!=='string'||!result.receipt_id)throw Error('Receipt belum dapat dipastikan. Coba ulang.');
      setReceipt(result.receipt_id);setUncertain(false);
    }catch(failure){setError(failure instanceof Error?failure.message:'Pengiriman belum dapat dipastikan.');if(submission.current)setUncertain(true);}
    finally{setPending(false);}
  }
  return <><a className="skip-link" href="#main">Lewati ke konten utama</a>
    <SigapiHeader reference={incident?.reference}><div className="page-intro"><div className="intro-labels"><span className="intro-eyebrow">KONFIRMASI PUBLIK</span></div><h1>Konfirmasi Laporan Kebakaran</h1><p>Bagikan kondisi yang Anda amati dari tempat aman.</p></div></SigapiHeader>
    <main id="main" className="page-shell"><div className="content-stack">
      {loading?<section className="panel" role="status">Memuat laporan...</section>:loadError?<section className="panel"><h1>{loadError}</h1><p>Periksa tautan atau coba muat ulang halaman.</p></section>:incident&&<>
        <div className="incident-context"><section className="panel incident-card"><div className="section-heading"><h2>Informasi Kejadian</h2><span className="status-badge">Belum dikonfirmasi resmi</span></div>
          <figure className="incident-photo">{incident.photo_url?<img src={incident.photo_url} alt="Dokumentasi kejadian yang disetujui untuk publik"/>:<div className="image-fallback"><Icon name="image" size={32}/><p>Dokumentasi belum tersedia untuk publik.</p></div>}</figure>
          <h3 className="incident-name">{incident.title}</h3><div className="incident-details"><p><Icon name="pin"/>{incident.location_name}</p><p><Icon name="calendar"/>{incident.observed_at?new Date(incident.observed_at).toLocaleString('id-ID',{timeZone:'Asia/Jakarta'}):'Waktu kejadian: Belum tersedia'}</p></div><p>{incident.summary}</p></section>
          <section className="panel incident-location-card"><h2>Lokasi Kejadian</h2><p className="section-description">Titik kejadian berbeda dengan lokasi Anda.</p><LiveMap {...incident.location}/></section>
        </div>
        <form className="verification-form" onSubmit={submit}>
          <section className="panel geolocation-card"><h2><Icon name="locate"/> Konfirmasi Lokasi Anda</h2><p className="section-description">Server memeriksa radius maksimal 2 km. Jangan mendekati api untuk memenuhi radius.</p>
            <div className={'location-status tone-'+(gps?'success':gpsError?'warning':'neutral')} role="status"><Icon name={locating?'loader':gps?'checkCircle':'locate'} className={locating?'spinner':undefined}/><div><strong>{locating?'Sedang mengambil lokasi...':gps?'Lokasi perangkat diperoleh. Menunggu pemeriksaan server.':gpsError||'Lokasi belum diperiksa'}</strong>{gps&&<p>Akurasi ±{Math.round(gps.coords.accuracy)} m. Izin lokasi tidak membuktikan identitas petugas.</p>}</div></div>
            <button type="button" className="button button-location w-full" onClick={locate} disabled={locating||locked}>{locating?'Mengambil Lokasi...':gps?'Perbarui Lokasi':'Aktifkan Lokasi'}</button>
          </section>
          <section className="panel confirmation-card"><fieldset disabled={locked} className="live-fields"><VerificationChoice choice={choice} solved={solved} onChoiceChange={value=>{setChoice(value);if(value!=='valid')setSolved(false);submission.current=null;}} onSolvedChange={setSolved}/>
            <div className="form-field"><label htmlFor="description">Keterangan tambahan <span className="optional">(opsional)</span></label><textarea id="description" rows={4} maxLength={2000} value={description} onChange={e=>{setDescription(e.target.value);submission.current=null;}}/><span className="character-count">{description.length} / 2.000 karakter</span></div>
            <PhotoUploadField onChange={value=>{setPhoto(value);submission.current=null;}}/></fieldset>
            {error&&<p className="field-error" role="alert">{error}</p>}{uncertain&&<p>Hasil kirim belum pasti. Isian dikunci agar pengulangan memakai ID permintaan yang sama.</p>}
            {receipt?<div className="location-status tone-success" role="status"><strong>Konfirmasi tersimpan. Receipt: {receipt}</strong><p>Kontribusi Anda menjadi informasi pendukung, bukan penutupan resmi.</p></div>:<button className="button button-primary w-full" type="submit" disabled={pending||(!uncertain&&(!gps||!choice))}>{pending?'Mengirim...':uncertain?'Periksa Ulang Pengiriman':'Kirim Konfirmasi'}<Icon name="arrow"/></button>}
          </section>
        </form><SafetyNotice/>
      </>}
    </div></main><PageFooter/></>;
}
