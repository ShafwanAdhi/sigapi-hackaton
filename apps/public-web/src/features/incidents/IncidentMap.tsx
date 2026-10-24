export function IncidentMap() {
  return (
    <figure className="map-figure">
      <div className="map-canvas">
        <svg viewBox="0 0 480 230" role="img" aria-labelledby="map-title map-description">
          <title id="map-title">Peta skematis lokasi simulasi di Kota Malang</title>
          <desc id="map-description">Susunan jalan dan titik kejadian bersifat ilustratif, bukan peta navigasi atau lokasi kebakaran nyata.</desc>
          <rect width="480" height="230" fill="#edf0e8" />
          <path d="M0 0h128l-26 79H0ZM318 0h162v64l-120 18ZM15 151l103-15 33 94H0ZM306 160l174-34v104H325Z" fill="#dce5d6" />
          <path d="M383-20c-21 53-62 64-37 105s-25 69-11 165" fill="none" stroke="#c2d8df" strokeWidth="17" />
          <g fill="none" stroke="#fffefa" strokeWidth="12">
            <path d="m-20 107 530-33M142-20l49 273M-20 207 530-48M-20 23l530 190" />
          </g>
          <g fill="none" stroke="#fffefa" strokeWidth="5">
            <path d="m39-10 47 250M267-10l20 260M445-10l-40 250M0 161l480-41M0 55l480 122" />
          </g>
          <circle cx="235" cy="115" r="55" fill="#d9a05a" fillOpacity=".12" stroke="#b77837" strokeDasharray="4 5" />
          <circle cx="235" cy="115" r="19" fill="#fdf9f1" />
          <path d="M235 95a13 13 0 0 0-13 13c0 10 13 22 13 22s13-12 13-22a13 13 0 0 0-13-13Z" fill="#a84e28" />
          <circle cx="235" cy="108" r="4" fill="white" />
          <text x="28" y="37" fill="#4c6155" fontSize="13" fontFamily="system-ui" fontWeight="600">KOTA MALANG</text>
          <text x="325" y="209" fill="#647467" fontSize="11" fontFamily="system-ui">Peta ilustratif</text>
        </svg>
        <span className="map-label">Titik kejadian simulasi</span>
      </div>
      <figcaption>Skema lokasi · bukan peta navigasi atau titik kejadian nyata.</figcaption>
    </figure>
  );
}
