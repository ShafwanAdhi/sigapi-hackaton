import { useEffect,useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export function LiveMap({latitude,longitude}:{latitude:number;longitude:number}) {
  const element=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    if(!element.current)return;
    const map=L.map(element.current,{scrollWheelZoom:false}).setView([latitude,longitude],14);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OpenStreetMap contributors',maxZoom:19}).addTo(map);
    L.circleMarker([latitude,longitude],{radius:10,color:'#C84B1B',fillColor:'#C84B1B',fillOpacity:.85}).addTo(map);
    L.circle([latitude,longitude],{radius:2000,color:'#1F4D45',weight:1,fillOpacity:.04}).addTo(map);
    const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(element.current);
    return()=>{observer.disconnect();map.remove();};
  },[latitude,longitude]);
  return <div ref={element} className="live-incident-map" role="img" aria-label="Peta titik kejadian dan radius konfirmasi 2 kilometer"/>;
}
