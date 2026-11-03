import {useEffect,useRef} from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type {Report} from './types';
export interface MapData {reports:Report[];boundary:GeoJSON.GeoJsonObject|null;firms:{points?:{latitude:number;longitude:number;acquired_at:string}[];sensor?:string;fetched_at?:string;coverage_end?:string}|null;}
export function FireMap({data,onReport}:{data:MapData;onReport?:(id:string)=>void}){
  const element=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    if(!element.current)return;
    const map=L.map(element.current,{scrollWheelZoom:false}).setView([-7.98,112.63],12);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OpenStreetMap contributors',maxZoom:19}).addTo(map);
    if(data.boundary)L.geoJSON(data.boundary,{style:{color:'#1F4D45',weight:1.5,fillOpacity:.03}}).addTo(map);
    const citizens=L.layerGroup().addTo(map),satellite=L.layerGroup().addTo(map);
    for(const report of data.reports){
      if(!report.location)continue;
      const marker=L.circleMarker([report.location.latitude,report.location.longitude],{radius:8,color:'#C84B1B',fillOpacity:.85,weight:2}).addTo(citizens);
      const content=document.createElement('button');content.type='button';content.className='map-report';content.textContent='Laporan '+report.id.slice(0,8)+' · '+(report.category==='building'?'Bangunan':'Hutan/lahan');
      content.onclick=()=>onReport?.(report.id);marker.bindPopup(content);
    }
    for(const hotspot of data.firms?.points??[]){
      const content=document.createElement('span');content.textContent=(data.firms?.sensor??'VIIRS')+' · '+hotspot.acquired_at+' · anomali panas';
      L.circleMarker([hotspot.latitude,hotspot.longitude],{radius:5,color:'#8A5A31',fillColor:'#FBE8DE',weight:1,fillOpacity:.85}).bindPopup(content).addTo(satellite);
    }
    L.control.layers({}, {'Laporan warga':citizens,'Hotspot satelit':satellite},{collapsed:false}).addTo(map);
    const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(element.current);
    return()=>{observer.disconnect();map.remove();};
  },[data,onReport]);
  return <div ref={element} className="fire-map" aria-label="Peta laporan warga dan hotspot satelit"/>;
}
