// Synthetic fixture only: this is not a report from a real citizen or emergency.
export const demoIncident = {
  slug: 'demo-malang-001',
  publicReference: 'SIGAPI-DEMO-001',
  title: 'Laporan kebakaran lahan',
  category: 'Kebakaran hutan / lahan',
  location: 'Area lahan terbuka, Kota Malang',
  locationDetail: 'Jawa Timur · area simulasi',
  reportedAt: '2026-10-24T14:20:00+07:00',
  summary:
    'Warga melaporkan asap dan api pada sebagian lahan berumput kering. Informasi kondisi lapangan masih memerlukan konfirmasi.',
  photoUrl: '/media/incident-simulation.webp',
  photoAlt:
    'Ilustrasi AI: asap dan api kecil pada lahan berumput, dilihat dari kejauhan. Bukan foto kejadian nyata.',
  isSimulation: true,
} as const;
