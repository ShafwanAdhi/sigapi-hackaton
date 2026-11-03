let csrf='';
export function setCsrf(value:string){csrf=value;}
export class ApiError extends Error {status:number;constructor(message:string,status:number){super(message);this.status=status;}}
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
  const mutation=options.method&&options.method!=='GET';
  const response=await fetch('/api/admin/'+path,{...options,credentials:'same-origin',
    headers:{...(options.body?{'Content-Type':'application/json'}:{}),...(mutation?{'X-CSRF-Token':csrf}:{}),...options.headers}});
  const data=await response.json();
  if(!response.ok){if(response.status===401)window.dispatchEvent(new Event('sigapi-unauthorized'));throw new ApiError(data.detail??'Permintaan gagal.',response.status);}
  return data as T;
}
