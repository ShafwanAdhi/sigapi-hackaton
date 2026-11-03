export interface User {username:string;region_code:string;csrf_token:string;}
export interface Report {id:string;status:string;created_at:string;revision:number;region_code:string;incident_id:string|null;
 location?:{latitude:number;longitude:number};category:string;risk:string;decision:{action?:string;reasons?:string[]};}
export interface Destination {id:string;name:string;number:string;role:'authority'|'community';categories:string[];active:boolean;authorized:boolean;version:number;address:string;invitation_url:string;}
export interface Runtime {settings:{distribution_enabled?:boolean;public_intake?:boolean};analysis_jobs:{state:string;count:number}[];approved_destinations:number;region_approved:boolean;live_gate:string;firms:{sensor?:string;coverage_end?:string;fetched_at?:string};heartbeats?:{service:string;last_seen:string}[];}
