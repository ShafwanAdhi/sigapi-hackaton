import type { DemoLocation, LocationState } from '../features/incidents/confirmation';

// Synthetic fixtures only. No real incident, GPS fix, server decision or receipt.
export const demoIncident = {
  slug: 'demo-insiden-sigapi',
  legacySlug: 'demo-malang-001',
  publicReference: 'SIGAPI-001',
  title: 'Laporan Kebakaran Lahan',
  location: 'Kota Malang, Jawa Timur',
  timeLabel: 'Waktu kejadian: Belum tersedia',
  status: 'Belum dikonfirmasi resmi',
  photoUrl: '/media/incident-simulation.webp',
  photoAlt: 'Asap dan api pada lahan berumput.',
  isSimulation: true,
} as const;

export const demoLocationOptions: { value: DemoLocation; label: string }[] = [
  { value: 'ready', label: 'Memenuhi persyaratan · 850 m' },
  { value: 'denied', label: 'Izin lokasi ditolak' },
  { value: 'outside', label: 'Di luar radius · 2,8 km' },
  { value: 'inaccurate', label: 'Akurasi belum memadai · 140 m' },
];

export const locationCopy: Record<LocationState, {
  title: string;
  description: string;
  tone: 'neutral' | 'info' | 'success' | 'warning' | 'danger';
}> = {
  idle: {
    title: 'Lokasi belum diperiksa',
    description: 'Aktifkan lokasi untuk mencoba tampilan pemeriksaan.',
    tone: 'neutral',
  },
  requesting: {
    title: 'Sedang mengambil lokasi perangkat...',
    description: 'Simulasi sedang berjalan. GPS perangkat tidak diakses.',
    tone: 'info',
  },
  ready: {
    title: 'Lokasi Anda memenuhi persyaratan konfirmasi.',
    description: 'Hasil simulasi: jarak 850 m, akurasi 25 m. Belum diperiksa oleh server.',
    tone: 'success',
  },
  denied: {
    title: 'Izin lokasi ditolak',
    description: 'Lokasi perangkat belum diizinkan. Aktifkan izin lokasi pada browser untuk mengirim konfirmasi.',
    tone: 'warning',
  },
  outside: {
    title: 'Di luar radius konfirmasi',
    description: 'Anda berada di luar radius konfirmasi 2 km dari titik kejadian. Konfirmasi tidak dapat dikirim.',
    tone: 'danger',
  },
  inaccurate: {
    title: 'Akurasi lokasi belum memadai',
    description: 'Akurasi lokasi belum memadai. Silakan coba perbarui lokasi perangkat.',
    tone: 'warning',
  },
};

export const locationSimulationDelay = 750;
